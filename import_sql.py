# -*- coding: UTF-8 -*-
import numpy as np
import chardet
import pandas as pd
import calendar
import datetime
import time
import re
import sqlalchemy.types as t
from sqlalchemy import create_engine


pd.set_option("display.max_columns", 5000)
pd.set_option("display.width", 5000)

engine = create_engine("mssql+pymssql://(local)/CHPA_1806")

df = pd.read_excel(open("data.xlsx", "rb"), sheet_name="全国")  # 从Excel读取数
print("Finished data reading...")
df = df.fillna(0)

df.set_index(
    [
        "TC I",
        "TC II",
        "TC III",
        "TC IV",
        "MOLECULE",
        "PRODUCT",
        "PACKAGE",
        "CORPORATION",
        "MANUF_TYPE",
        "FORMULATION",
        "STRENGTH",
    ],
    inplace=True,
)
df = df.stack().reset_index()

new = df["level_11"].str.split("_", expand=True)
df["UNIT"] = new[0]
df["PERIOD"] = new[1]
df["DATE"] = new[2]
df["DATE"] = (
    (
        pd.to_numeric(df["DATE"].str[-2:], errors="coerce").fillna(0).astype(np.int64)
        + 2000
    )
    * 10000
    + pd.to_numeric(df["DATE"].str[:-2], errors="coerce").fillna(0).astype(np.int64)
    * 100
    + 1
)
df["DATE"] = pd.to_datetime(df["DATE"], format="%Y%m%d")
df["MOLECULE_TC"] = df["MOLECULE"] + " （" + df["TC IV"].str[:4] + "）"
df["PRODUCT_CORP"] = df["PRODUCT"].str[:-3] + " （" + df["CORPORATION"] + "）"

df.drop("level_11", axis=1, inplace=True)
df.columns = [
    "TC I",
    "TC II",
    "TC III",
    "TC IV",
    "MOLECULE",
    "PRODUCT",
    "PACKAGE",
    "CORPORATION",
    "MANUF_TYPE",
    "FORMULATION",
    "STRENGTH",
    "AMOUNT",
    "UNIT",
    "PERIOD",
    "DATE",
    "MOLECULE_TC",
    "PRODUCT_CORP",
]

df_volume = df[df["UNIT"] == "Volume"]
df_volume.loc[:, "UNIT"] = "Volume (Counting Unit)"
df_volume.loc[:, "TEMP"] = df_volume.loc[:, "PACKAGE"].str.split().str[-1]

df1 = df_volume[df_volume["TEMP"].str.isnumeric()]
df2 = df_volume[df_volume["TEMP"].str.isnumeric() == False]
df1["TEMP"] = df1["TEMP"].apply(np.int64)
df1["AMOUNT"] = df1["AMOUNT"] * df1["TEMP"]
df_volume = pd.concat([df1, df2])
df_volume.drop("TEMP", axis=1, inplace=True)
df_combined = pd.concat([df, df_volume])
print(df_combined)

print("start importing...")
df_combined.to_sql(
    "data",
    con=engine,
    if_exists="replace",
    index=False,
    dtype={
        "DATE": t.DateTime(),
        "AMOUNT": t.FLOAT(),
        "TC I": t.NVARCHAR(length=200),
        "TC II": t.NVARCHAR(length=200),
        "TC III": t.NVARCHAR(length=200),
        "TC IV": t.NVARCHAR(length=200),
        "MOLECULE": t.NVARCHAR(length=200),
        "PRODUCT": t.NVARCHAR(length=200),
        "PACKAGE": t.NVARCHAR(length=200),
        "CORPORATION": t.NVARCHAR(length=200),
        "MANUF_TYPE": t.NVARCHAR(length=20),
        "FORMULATION": t.NVARCHAR(length=50),
        "STRENGTH": t.NVARCHAR(length=20),
        "UNIT": t.NVARCHAR(length=25),
        "PERIOD": t.NVARCHAR(length=3),
        "MOLECULE_TC": t.NVARCHAR(length=255),
        "PRODUCT_CORP": t.NVARCHAR(length=255),
    },
)


# #预处理和导入城市数据
# df = pd.read_excel(open('data_city.xlsx', 'rb'), sheet_name='城市')  #从Excel读取数
# print('Finished data reading...')
# d = {#'data_city_ARB': df['TC III']=='C09C ANGIOTENS-II ANTAG, PLAIN|血管紧张素II拮抗剂，单一用药'
#        # 'data_city_Levetiracetam': df['MOLECULE']=='左乙拉西坦|LEVETIRACETAM',
#        # 'data_city_ep': df['TC IV']=='N03A0 ANTI-EPILEPTICS|抗癫痫药物',
#        # 'data_city_A10': df['TC II'] == 'A10 DRUGS USED IN DIABETES|糖尿病用药',
#        # 'data_city_NIAD': df['TC III'].isin([
#        #        'A10L A-GLUCOSIDASE INH A-DIAB|α-葡糖苷酶抑制剂(A10B5)',
#        #        'A10K GLITAZONE ANTIDIABETICS|格列酮类降糖药',
#        #        'A10M GLINIDE ANTIDIABETICS|格列奈类降糖药',
#        #        'A10S GLP-1 AGONIST A-DIABS|GLP-1激动剂(胰高血糖素样肽-1激动剂类降糖药)(A10B9)',
#        #        'A10N DPP-IV INHIBITOR A-DIABS|DPP-IV（二肽基肽酶IV）抑制剂',
#        #        'A10P SGLT2 INHIBITOR A-DIABS|钠-葡萄糖协同转运蛋白2抑制剂',
#        #        'A10H SULPHONYLUREA A-DIABS|磺脲类降糖药(A10B1)',
#        #        'A10J BIGUANIDE ANTIDIABETICS|双胍类降糖药',
#        # ]),
#        'data_city_INS': df['TC III'].isin([
#               'A10D ANIMAL INSULINS|动物胰岛素',
#               'A10C HUMAN INSULIN+ANALOGUES|人胰岛素和类似物',
#               'A10E INSULIN DEVICES|胰岛素设备',
#        ])
# }
# # mask = (df['TC III']=='B01B HEPARINS|肝素')|(df['MOLECULE']=='比伐芦定|BIVALIRUDIN')
# # mask = (df['TC III']=='C09A ACE INHIBITORS PLAIN|血管紧张素转换酶抑制剂，单一用药')|(df['TC III']=='C09C ANGIOTENS-II ANTAG, PLAIN|血管紧张素II拮抗剂，单一用药')
# # mask = df['TC IV']=='C10A1 STATINS (HMG-COA RED)|他汀类(HMG-COA（羟-甲戊二酰辅酶A）还原酶抑制剂)'
# # mask = df['TC II']=='R03 ANTI-ASTHMA & COPD PROD|抗哮喘和COPD(慢性阻塞性肺疾病) 药'
# # mask = (df['MOLECULE'].isin(['氢氯吡格雷|CLOPIDOGREL','替格瑞洛|TICAGRELOR']))|(df['PRODUCT']=='拜阿司匹灵|BAYASPIRIN         BAY')
# # mask = (df['TC IV'] == 'B01F0 DIRECT FACTOR XA INHIBS|直接因子XA抑制剂')|(df['MOLECULE'].isin(['华法林|WARFARIN','达比加群酯|DABIGATRAN ETEXILATE']))
# # mask = df['TC IV'] == 'C09D9 AT2 ANTG COMB OTH DRUGS|血管紧张素II拮抗剂与其他药联用'
# # mask = df['TC III'] == 'M05B BONE CALCIUM REGULATORS|骨钙调节剂'
# # mask = df['PRODUCT'].isin(['宝丽亚|CLENIL             C5I', '普米克令舒|PULMICORT RESP     AZN', '辅舒酮|FLIXOTIDE          GSK'])
# # mask = df['TC III']=='C09C ANGIOTENS-II ANTAG, PLAIN|血管紧张素II拮抗剂，单一用药'
#
# for key,value in d.items():
#        df = df.loc[value]
#        print(df)
#        df.set_index(['CITY', 'TC I', 'TC II', 'TC III',	'TC IV', 'MOLECULE',	'PRODUCT',	'PACKAGE',	'CORPORATION', 'MANUF_TYPE', 'FORMULATION', 'STRENGTH'], inplace=True)
#        df = df.stack().reset_index()
#        print(df)
#        new=df['level_12'].str.split('_', expand=True)
#        df['UNIT'] = new[0]
#        df['PERIOD'] = new[1]
#        df['DATE'] = new[2]
#        df['DATE'] = (pd.to_numeric(df['DATE'].str[-2:], errors='coerce').fillna(0).astype(np.int64)+2000)*10000+pd.to_numeric(df['DATE'].str[:-2], errors='coerce').fillna(0).astype(np.int64)*100+1
#        df['DATE'] = pd.to_datetime(df['DATE'], format="%Y%m%d")
#        df['MOLECULE_TC'] = df['MOLECULE'] + ' （'+ df['TC IV'].str[:4] + '）'
#        df['PRODUCT_CORP'] = df['PRODUCT'].str[:-3] + ' （'+ df['CORPORATION'] + '）'
#
#        df.drop('level_12', axis=1, inplace=True)
#        df.columns = ['CITY', 'TC I', 'TC II', 'TC III',	'TC IV', 'MOLECULE',	'PRODUCT',	'PACKAGE',	'CORPORATION', 'MANUF_TYPE',
#                      'FORMULATION', 'STRENGTH', 'AMOUNT', 'UNIT', 'PERIOD', 'DATE', 'MOLECULE_TC', 'PRODUCT_CORP']
#
#        print(df)
#        print('start importing...')
#
#        df.to_sql(key, con=engine, if_exists='replace', index=False,
#                  dtype={'CITY': t.NVARCHAR(length=5),
#                         'DATE': t.DateTime(),
#                         'AMOUNT': t.FLOAT(),
#                         'TC I': t.NVARCHAR(length=200),
#                         'TC II': t.NVARCHAR(length=200),
#                         'TC III': t.NVARCHAR(length=200),
#                         'TC IV': t.NVARCHAR(length=200),
#                         'MOLECULE': t.NVARCHAR(length=200),
#                         'PRODUCT': t.NVARCHAR(length=200),
#                         'PACKAGE': t.NVARCHAR(length=200),
#                         'CORPORATION': t.NVARCHAR(length=200),
#                         'MANUF_TYPE': t.NVARCHAR(length=20),
#                         'FORMULATION': t.NVARCHAR(length=50),
#                         'STRENGTH': t.NVARCHAR(length=20),
#                         'UNIT': t.NVARCHAR(length=6),
#                         'PERIOD': t.NVARCHAR(length=3),
#                         'MOLECULE_TC': t.NVARCHAR(length=255),
#                         'PRODUCT_CORP': t.NVARCHAR(length=255),
#                         }
#                  )


print(time.process_time())

# def get_agg_df(date, unit, period):
#     df_new = pd.DataFrame()
#     sql = "SELECT * FROM data_city_RAAS_Plain"
#     df = pd.read_sql(sql=sql, con=engine)
#     # df['DATE'] = pd.to_datetime(df['date'])
#     mask_mat_value_latest = (df['DATE'] == date) & (df['UNIT'] == unit) & (df['PERIOD'] == period)
#     df_mat_value_latest = df.loc[mask_mat_value_latest]
#     table_mat_value_latest_class = pd.pivot_table(df_mat_value_latest, values='AMOUNT', index='CITY', columns='TC III', aggfunc=np.sum)
#
#     df_new['RAAS_Plain_Sales'] = table_mat_value_latest_class.sum(axis=1)
#     df_new['ARB_Sales'] = table_mat_value_latest_class.loc[:,'C09C ANGIOTENS-II ANTAG, PLAIN|血管紧张素II拮抗剂，单一用药']
#     df_new['ACEI_Sales'] = table_mat_value_latest_class.loc[:,'C09A ACE INHIBITORS PLAIN|血管紧张素转换酶抑制剂，单一用药']
#     df_new['ARB_Share'] = df_new['ARB_Sales']/df_new['RAAS_Plain_Sales']
#     df_new['ACEI_Share'] = df_new['ACEI_Sales']/df_new['RAAS_Plain_Sales']
#
#     table_mat_value_latest_product = pd.pivot_table(df_mat_value_latest, values='AMOUNT', index='CITY', columns='PRODUCT', aggfunc=np.sum)
#     df_new['XinLiTan_Sales'] = table_mat_value_latest_product.loc[:,'信立坦|XIN LI TAN         SI6']
#     df_new['XinLiTan_Share'] = df_new['XinLiTan_Sales']/df_new['RAAS_Plain_Sales']
#
#     return df_new
#
# df_latest = get_agg_df('2018-12-1','Value','MAT')
# df_diff = get_agg_df('2018-12-1','Value','MAT') - get_agg_df('2017-12-1','Value','MAT')
# df_diff.columns = df_diff.columns + '_Uplift'
# df_gr = get_agg_df('2018-12-1','Value','MAT')/get_agg_df('2017-12-1','Value','MAT') - 1
# df_gr.columns = df_gr.columns + '_GR'
# df_combined = pd.concat([df_latest, df_diff, df_gr], axis=1)
# print(df_combined)
# df_combined.drop(['ARB_Share_GR', 'ACEI_Share_GR', 'XinLiTan_Share_GR'], axis=1, inplace=True)
#
# df_combined['XinLiTan EI'] = (df_combined['XinLiTan_Sales_GR'] + 1)/(df_combined['RAAS_Plain_Sales_GR'] + 1)*100
# df_combined['CITY'] = df_combined.index
# df_combined.replace([np.inf, -np.inf], np.nan, inplace=True)
# print(df_combined)
# df_combined.to_sql('data_city_RAAS_Plain_agg', con=engine, if_exists='replace', index=False,
#                     dtype={'CITY': t.NVARCHAR(length=5),
#
#                          }
#                     )
#
# end = time.clock()
# print(end-start)
