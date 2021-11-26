from django.shortcuts import render
import pandas as pd


if __name__ == "__main__":
    df = pd.read_excel("./test.xlsx")
    print(df["爬取日期"])