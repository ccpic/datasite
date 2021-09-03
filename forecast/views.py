from django.shortcuts import render
import pandas as pd
import openpyxl
from itertools import islice, product
import statsmodels.api as sm
import matplotlib.pyplot as plt

def index(request):
    if "GET" == request.method:
        return render(request, "forecast/index.html", {})
    else:
        excel_file = request.FILES["excel_file"]

        wb = openpyxl.load_workbook(excel_file)
        ws = wb.active

        data = ws.values
        cols = next(data)[1:]
        data = list(data)
        idx = [r[0] for r in data]
        data = (islice(r, 1, None) for r in data)
        df = pd.DataFrame(data, index=idx, columns=cols)
        print(df)

        p = d = q = range(0, 2)
        pdq = list(product(p, d, q))
        seasonal_pdq = [(x[0], x[1], x[2], 3) for x in list(product(p, d, q))]

        AIC_result = []
        for param in pdq:
            for param_seasonal in seasonal_pdq:
                try:
                    mod = sm.tsa.statespace.SARIMAX(
                        df,
                        order=param,
                        seasonal_order=param_seasonal,
                        enforce_stationarity=False,
                        enforce_invertibility=False,
                    )
                    results = mod.fit()
                    AIC_result.append(
                        "ARIMA{}x{}3 - AIC:{}".format(
                            param, param_seasonal, results.aic
                        )
                    )
                except:
                    continue

        mod = sm.tsa.statespace.SARIMAX(
            df, order=(0, 1, 1), seasonal_order=(0, 1, 1, 3), enforce_stationarity=False, enforce_invertibility=False
        )
        results = mod.fit()
        print(results.summary().tables[1])

        
        month=7
        pred_uc = results.get_forecast(steps=12 + (12 - month))
        pred_ci = pred_uc.conf_int()
        ax = df.plot(label="observed", figsize=(14, 9))
        pred_uc.predicted_mean.plot(ax=ax, label="Forecast")
        ax.fill_between(pred_ci.index, pred_ci.iloc[:, 0], pred_ci.iloc[:, 1], color="k", alpha=0.25)
        ax.set_xlabel("Date")
        ax.set_ylabel("Sales")
        plt.legend()
        plt.show()

        y_forecasted = pred_uc.predicted_mean
        print(y_forecasted)
        
        context = {
            "table_data": df.to_html(),
            "AIC_result": AIC_result,
        }

        return render(request, "forecast/index.html", context)

