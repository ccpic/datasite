from django.shortcuts import render
from django.http import JsonResponse
import math


def index(request):
    return render(request, 'price_calc/calc.html')


def ajax_calc(request):
    number_bm=request.GET['number_bm']
    price_bm=request.GET['price_bm']
    number_ta = request.GET['number_ta']
    strength_bm = request.GET['strength_bm']
    strength_ta = request.GET['strength_ta']

    uprice_bm = float(price_bm)/float(number_bm)
    x1 = float(number_ta)/float(number_bm)
    l1 = math.log(x1, 2)
    k1 = math.pow(1.95, l1)
    x2 = float(strength_ta)/float(strength_bm)
    l2 = math.log(x2,2)
    k2 = math.pow(1.7, l2)
    price_ta = round(float(price_bm)*k1*k2, 2)
    uprice_ta = round(price_ta/float(number_ta), 2)
    uprice_bm = round(uprice_bm, 2)

    dict_result = {'uprice_bm': uprice_bm,
                   'price_ta': price_ta,
                   'uprice_ta': uprice_ta}
    return JsonResponse(dict_result)