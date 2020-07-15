#!/usr/bin/env python
import os
import time
from sqlalchemy import  create_engine
import pandas as pd
import django


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "datasite.settings")
django.setup()

from chpa_data.models import *

engine = create_engine('mssql+pymssql://(local)/CHPA_1806')
table = 'data'


# def importCity():
#     sql = "SELECT Distinct City FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import City
#
#     l = []
#     for city in df.values:
#         l.append(City(cname=city[0], ename=''))
#
#     City.objects.bulk_create(l)
#
#
# def importCorp():
#     sql = "SELECT Distinct CORPORATION FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import Corporation
#
#     l = []
#     for corp in df.values:
#         l.append(Corporation(cname=corp[0].split('|')[0], ename=corp[0].split('|')[1]))
#
#
#     Corporation.objects.bulk_create(l)
#
#
# def importManufType():
#     sql = "SELECT Distinct Manuf_type FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import Manuf_type
#
#     l = []
#     for manuf_type in df.values:
#         l.append(Manuf_type(cname='', ename=manuf_type[0]))
#
#
#     Manuf_type.objects.bulk_create(l)
#
#
# def importFormulation():
#     sql = "SELECT Distinct Formulation FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import Formulation
#
#     l = []
#     for formulation in df.values:
#         l.append(Formulation(cname='', ename=formulation[0]))
#
#
#     Formulation.objects.bulk_create(l)
#
#
# def importTCI():
#     sql = "SELECT Distinct [TC I] FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import TC_I
#
#     l = []
#     for tc in df.values:
#         text = tc[0]
#         code = text[0]
#         cname = text.split('|')[1]
#         ename = text.split('|')[0][2:]
#         l.append(TC_I(code=code, cname=cname, ename=ename))
#
#
#     TC_I.objects.bulk_create(l)
#
#
# def importTCII():
#     sql = "SELECT Distinct [TC I], [TC II] FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import TC_I, TC_II
#
#     l = []
#     for tc in df.values:
#         text = tc[1]
#         code = text[:3]
#         cname = text.split('|')[1]
#         ename = text.split('|')[0][4:]
#         l.append(TC_II(code=code, cname=cname, ename=ename, tc_i=TC_I.objects.get(cname=tc[0].split('|')[1])))
#
#
#     TC_II.objects.bulk_create(l)
#
#
# def importTCIII():
#     sql = "SELECT Distinct [TC II], [TC III] FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import TC_II, TC_III
#
#     l = []
#     for tc in df.values:
#         text = tc[1]
#         code = text[:4]
#         cname = text.split('|')[1]
#         ename = text.split('|')[0][5:]
#         l.append(TC_III(code=code, cname=cname, ename=ename, tc_ii=TC_II.objects.get(cname=tc[0].split('|')[1])))
#
#
#     TC_III.objects.bulk_create(l)
#
#
# def importTCIV():
#     sql = "SELECT Distinct [TC III], [TC IV] FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import TC_III, TC_IV
#
#     l = []
#     for tc in df.values:
#         text = tc[1]
#         code = text[:5]
#         cname = text.split('|')[1]
#         ename = text.split('|')[0][6:]
#         l.append(TC_IV(code=code, cname=cname, ename=ename, tc_iii=TC_III.objects.get(cname=tc[0].split('|')[1])))
#
#
#     TC_IV.objects.bulk_create(l)
#
#
# def importMOLECULE():
#     sql = "SELECT Distinct [TC IV],MOLECULE FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import TC_IV, Molecule
#
#     l = []
#
#     for molecule in df.values:
#         text = molecule[1]
#         cname = text.split('|')[0]
#         ename = text.split('|')[1]
#         tc_code = molecule[0][:5]
#         l.append(Molecule(cname=cname, ename=ename, tc_iv=TC_IV.objects.get(cname=molecule[0].split('|')[1])))
#
#     Molecule.objects.bulk_create(l)
#
#     # ThroughModel = Molecule.tc_iv.through
#     # through_models = []
#     # for molecule in df.values:
#     #     tc_code = molecule[0][:5]
#     #     for molecule in Molecule.objects.all():
#     #         through_models.append(ThroughModel(tc_iv_id=tc.id, molecule_id=Molecule.objects.get(cname=cname).id))
#
#
# # def importMOLECULETC():
# #     sql = "SELECT Distinct [TC IV],MOLECULE FROM "+table
# #     df = pd.read_sql(sql=sql, con=engine)
# #
# #     from data_viz.models import TC_IV, Molecule, MoleculeTC
# #
# #     l = []
# #
# #     for molecule in df.values:
# #         text = molecule[1]
# #         cname = text.split('|')[0]
# #         ename = text.split('|')[1]
# #         tc_code = molecule[0][:5]
# #         l.append(MoleculeTC(molecule=Molecule.objects.filter(cname=cname, ename=ename).first(), tc_iv=TC_IV.objects.get(code=tc_code)))
# #
# #     MoleculeTC.objects.bulk_create(l)
#
#
# def importProduct():
#     sql = "SELECT Distinct PRODUCT, MOLECULE, CORPORATION, MANUF_TYPE, [TC IV] FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import Product, Molecule, Corporation, Manuf_type, TC_IV
#
#     l = []
#
#     for record in df.values:
#         product_text = record[0]
#         cname = product_text.split('|')[0]
#         ename = product_text.split('|')[1][:-3].rstrip()
#         molecule_cname = record[1].split('|')[0]
#         molecule_ename = record[1].split('|')[1]
#         corp_cname = record[2].split('|')[0]
#         mt_ename = record[3]
#         tc4_cname = record[4].split('|')[1]
#         print(cname, molecule_ename, tc4_cname, Molecule.objects.get(cname=molecule_cname, ename=molecule_ename, tc_iv=TC_IV.objects.get(cname=tc4_cname)))
#         l.append(Product(cname=cname, ename=ename,
#                          molecule=Molecule.objects.get(cname=molecule_cname, ename=molecule_ename, tc_iv=TC_IV.objects.get(cname=tc4_cname)),
#                          corporation=Corporation.objects.get(cname=corp_cname),
#                          manuf_type = Manuf_type.objects.get(ename=mt_ename)
#                          ))
#
#     Product.objects.bulk_create(l)
#
#
# def importPack():
#     sql = "SELECT Distinct PRODUCT, PACKAGE, MOLECULE, CORPORATION, FORMULATION, STRENGTH, [TC IV], MANUF_TYPE FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import Product, Package, Formulation, Corporation, Molecule, TC_IV, Manuf_type
#
#     l = []
#
#     for record in df.values:
#         product_text = record[0]
#         product_cname = product_text.split('|')[0]
#         product_ename = product_text.split('|')[1][:-3].rstrip()
#         package_text = record[1]
#         package_desc = package_text.split('|')[1][(len(product_ename)+1):]
#         molecule_cname = record[2].split('|')[0]
#         molecule_ename = record[2].split('|')[1]
#         corp_cname = record[3].split('|')[0]
#         formulation = record[4]
#         strength = record[5]
#         tc4_cname = record[6].split('|')[1]
#         mt_ename = record[7]
#         l.append(Package(desc=package_desc,
#                          product=Product.objects.filter(cname=product_cname, ename=product_ename,
#                                          molecule=Molecule.objects.get(cname=molecule_cname, ename=molecule_ename,
#                                                           tc_iv=TC_IV.objects.get(cname=tc4_cname)),
#                                          corporation=Corporation.objects.get(cname=corp_cname),
#                                          manuf_type=Manuf_type.objects.get(ename=mt_ename)).first(),
#                          formulation=Formulation.objects.get(ename=formulation),
#                          strength=strength
#                          ))
#
#     Package.objects.bulk_create(l)
#
#
# def importSales():
#     sql = "SELECT * FROM "+table
#     df = pd.read_sql(sql=sql, con=engine)
#
#     from data_viz.models import Product, Package, Formulation, Corporation, Molecule, TC_IV, Manuf_type, Sales, City
#
#     l = []
#     count = 0
#     for record in df.values:
#         count += 1
#         city_cname = record[0]
#         tc4_cname = record[4].split('|')[1]
#         molecule_cname = record[5].split('|')[0]
#         molecule_ename = record[5].split('|')[1]
#         product_cname = record[6].split('|')[0]
#         product_ename = record[6].split('|')[1][:-3].rstrip()
#         package_desc =  record[7].split('|')[1][(len(product_ename)+1):]
#         corp_cname = record[8].split('|')[0]
#         mt_ename = record[9]
#         formulation_ename = record[10]
#         amount = record[12]
#         unit = record[13]
#         period = record[14]
#         date = record[15]
#         # print(count, city_cname, product_cname, package_desc, unit, period, date, amount)
#
#         l.append(Sales(city=City.objects.get(cname=city_cname),
#                        package=Package.objects.get(desc=package_desc,
#                                                    product=Product.objects.filter(cname=product_cname, ename=product_ename,
#                                                                                   molecule=Molecule.objects.get(cname=molecule_cname, ename=molecule_ename,
#                                                                                                                 tc_iv=TC_IV.objects.get(cname=tc4_cname)),
#                                                                                   corporation=Corporation.objects.get(cname=corp_cname),
#                                                                                   manuf_type=Manuf_type.objects.get(ename=mt_ename)).first(),
#                                                    formulation=Formulation.objects.get(ename=formulation_ename),
#                                                    ),
#                        amount=amount,
#                        date=date,
#                        unit=unit,
#                        period=period
#                        ))
#
#     Sales.objects.bulk_create(l)


def importModel(dict):
    for key in dict:
        sql = "SELECT Distinct [" + key + "] FROM "+table
        df = pd.read_sql(sql=sql, con=engine)
        df.dropna(inplace=True)
        print(df)
        l = []
        for item in df.values:
            l.append(dict[key](name=item[0]))

        dict[key].objects.bulk_create(l)


if __name__ == "__main__":
    start = time.clock()
    # importCity()
    # importCorp()
    # importManufType()
    # importFormulation()
    # importTCI()
    # importTCII()
    # importTCIII()
    # importTCIV()
    # importMOLECULE()
    # importProduct()
    # importPack()
    importModel(d_model)
    print('Done!', time.clock()-start)