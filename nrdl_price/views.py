from django.shortcuts import render
from django.http import request

def index(request: request):
    context = {}
    return render(request, "nrdl_price/index.html", context)
