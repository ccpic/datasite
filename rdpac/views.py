from vbp.views import DISPLAY_LENGTH
from django.shortcuts import render, HttpResponse
from .models import Company, Drug, Sales, CURRENT_YEAR
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core import serializers
import json


@login_required
def index(request):
    companies = Company.objects.all()
    try:
        companies_ranked = sorted(
            companies, key=lambda x: x.latest_annual_netsales, reverse=True
        )  # 按最新年份销售由高到低排序
    except:
        companies_ranked = None
    sales_ranked = Sales.objects.filter(year=CURRENT_YEAR).order_by("-netsales_value")
    # drugs_ranked = sorted(drugs, key=lambda x: x.annual_netsales, reverse=True) # 按最新年份销售由高到低排序
    context = {
        "companies_ranked": companies_ranked,
        "sales_ranked": sales_ranked,
        "CURRENT_YEAR": CURRENT_YEAR,
    }
    return render(request, "rdpac/index.html", context)


@login_required
def drug_detail(request, drug_id):
    drug = Drug.objects.get(pk=drug_id)
    sales = drug.sales.all()
    context = {
        "drug": drug,
        "sales": sales,
    }
    return render(request, "rdpac/drug_detail.html", context)


@login_required
def company(request):
    pass


@login_required
def drug(request):
    pass


@login_required
def company_detail(request, company_id):
    company = Company.objects.get(pk=company_id)
    sales = company.sales.all()
    context = {
        "company": company,
        "sales": sales,
    }
    return render(request, "rdpac/company_detail.html", context)


@login_required
def search(request, kw):
    print(kw)
    # kw = request.POST.get("kw")
    company_result = Company.objects.filter(
        Q(name_en__icontains=kw)  # 搜索公司英文名
        | Q(name_cn__icontains=kw)  # 搜索公司中文名
        | Q(abbr__icontains=kw)  # 搜索公司简称
    ).distinct()

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinc(),order_by()等queryset时出现重复对象的bug
    sr_ids = [company.id for company in company_result]
    company_result2 = Company.objects.filter(id__in=sr_ids)

    drug_result = Drug.objects.filter(
        Q(molecule_en__icontains=kw)  # 搜索药品英文通用名
        | Q(molecule_cn__icontains=kw)  # 搜索药品中文通用名
        | Q(product_name_en__icontains=kw)  # 搜索药品英文产品名
        | Q(product_name_cn__icontains=kw)  # 搜索药品中文产品名
    )

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinc(),order_by()等queryset时出现重复对象的bug
    sr_ids = [drug.id for drug in drug_result]
    drug_result2 = Drug.objects.filter(id__in=sr_ids)

    objs = list(company_result2) + list(drug_result2)
    try:
        data = serializers.serialize("json", objs, ensure_ascii=False)
        res = {
            "data": data,
            "code": 200,
        }
        print(objs)
    except Exception as e:
        res = {
            "errMsg": e,
            "code": 0,
        }
    return HttpResponse(
        json.dumps(res, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )
    # elif request.method == "GET":
    #     DISPLAY_LENGTH = 25
    #     HOT_KWS = ["诺欣妥"]
    #     paginator = Paginator(
    #         search_result2, DISPLAY_LENGTH
    #     )  #  为了克服pagination bug这里的参数时search_result2
    #     page = request.GET.get("page")

    #     try:
    #         rows = paginator.page(page)
    #     except PageNotAnInteger:
    #         rows = paginator.page(1)
    #     except EmptyPage:
    #         rows = paginator.page(paginator.num_pages)

    #     context = {
    #         "tenders": rows,
    #         "num_pages": paginator.num_pages,
    #         "record_n": paginator.count,
    #         "display_length": DISPLAY_LENGTH,
    #         "kw": kw,
    #         "hot_kws": HOT_KWS,
    #     }

    #     return render(request, "vbp/tenders.html", context)
