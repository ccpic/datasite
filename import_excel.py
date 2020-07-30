import pandas as pd

for i in range(31):
    print(i)
    df1 = pd.read_excel('第三批地方报量.xlsx', sheet_name='Table ' + str(i+1), header=0)
    province = df1.columns[0][:-23]
    df2 = pd.read_excel('第三批地方报量.xlsx', sheet_name='Table '+ str(i+1), header=1)
    df2 = df2.fillna(method='ffill')
    df2 = df2[['品种名称', '规格', '首年约定采购量计算基数']]
    df2['地区'] = province
    if i == 0:
        df_combined = df2
    else:
        df_combined = pd.concat([df_combined, df2], axis=0)

df_combined.to_csv('result.csv', index=False, encoding="utf_8_sig")