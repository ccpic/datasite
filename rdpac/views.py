from django.shortcuts import render, HttpResponse
from .models import Company, Drug, Sales, TC_III, CURRENT_YEAR
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, Q
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.core import serializers
import json

TOP_N = 10


@login_required
def index(request):
    companies = Company.objects.all()
    try:
        companies_ranked = sorted(
            companies, key=lambda x: x.latest_annual_netsales, reverse=True
        )[
            :TOP_N
        ]  # 按最新年份销售由高到低排序
    except:
        companies_ranked = None

    print(companies_ranked)

    tc_iiis = TC_III.objects.filter(drugs__isnull=False).distinct()  # 所有有关联药物存在的TC3
    tc_iiis_ranked = sorted(
        tc_iiis, key=lambda x: x.latest_annual_netsales, reverse=True
    )[
        :TOP_N
    ]  # 按最新年份销售由高到低排序

    sales_ranked = Sales.objects.filter(year=CURRENT_YEAR).order_by("-netsales_value")[
        :TOP_N
    ]
    # drugs_ranked = sorted(drugs, key=lambda x: x.annual_netsales, reverse=True) # 按最新年份销售由高到低排序
    context = {
        "companies_ranked": companies_ranked,
        "tc_iiis_ranked": tc_iiis_ranked,
        "sales_ranked": sales_ranked,
        "CURRENT_YEAR": CURRENT_YEAR,
    }
    return render(request, "rdpac/rank.html", context)


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
    companies = Company.objects.all()
    try:
        companies_ranked = sorted(
            companies, key=lambda x: x.latest_annual_netsales, reverse=True
        )  # 按最新年份销售由高到低排序
    except:
        companies_ranked = None

    context = {
        "companies_ranked": companies_ranked,
        "CURRENT_YEAR": CURRENT_YEAR,
    }
    return render(request, "rdpac/company.html", context)


@login_required
def drug(request):
    sales_ranked = Sales.objects.filter(year=CURRENT_YEAR).order_by("-netsales_value")

    context = {
        "sales_ranked": sales_ranked,
        "CURRENT_YEAR": CURRENT_YEAR,
    }
    return render(request, "rdpac/drug.html", context)


@login_required
def tc_iii(request):
    tc_iiis = TC_III.objects.filter(drugs__isnull=False).distinct()  # 所有有关联药物存在的TC3
    tc_iiis_ranked = sorted(
        tc_iiis, key=lambda x: x.latest_annual_netsales, reverse=True
    )  # 按最新年份销售由高到低排序

    context = {
        "tc_iiis_ranked": tc_iiis_ranked,
        "CURRENT_YEAR": CURRENT_YEAR,
    }
    return render(request, "rdpac/tc_iii.html", context)


@login_required
def company_detail(request, company_id):
    company = Company.objects.get(pk=company_id)

    context = {
        "company": company,
        "CURRENT_YEAR": CURRENT_YEAR,
    }
    return render(request, "rdpac/company_detail.html", context)


@login_required
def tc_iii_detail(request, tc_iii_id):
    tc_iii = TC_III.objects.get(pk=tc_iii_id)

    context = {
        "tc_iii": tc_iii,
        "CURRENT_YEAR": CURRENT_YEAR,
    }
    return render(request, "rdpac/tc_iii_detail.html", context)


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
        | Q(tc_iii__code__icontains=kw)  # 搜索TC3 Code
        | Q(tc_iii__name_cn__icontains=kw)  # 搜索TC3中文名
        | Q(tc_iii__name_en__icontains=kw)  # 搜索TC3英文名
    )

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinc(),order_by()等queryset时出现重复对象的bug
    sr_ids = [drug.id for drug in drug_result]
    drug_result2 = Drug.objects.filter(id__in=sr_ids)

    tc_iii_result = (
        TC_III.objects.filter(drugs__isnull=False) # TC III必须是有数据的
        .filter(
            Q(name_en__icontains=kw)  # 搜索TC3英文名
            | Q(name_cn__icontains=kw)  # 搜索TC3中文名
            | Q(code__icontains=kw)  # 搜索TC3 Code
        )
        .distinct()
    )

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinc(),order_by()等queryset时出现重复对象的bug
    sr_ids = [tc_iii.id for tc_iii in tc_iii_result]
    tc_iii_result2 = TC_III.objects.filter(id__in=sr_ids)

    objs = list(company_result2) + list(tc_iii_result2) + list(drug_result2)
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


if __name__ == "__main__":
    TOP_N = 10
    tc_iiis = TC_III.objects.all()
    try:
        tc_iiis_ranked = sorted(
            tc_iiis, key=lambda x: x.latest_annual_netsales, reverse=True
        )[
            :TOP_N
        ]  # 按最新年份销售由高到低排序
    except:
        tc_iiis_ranked = None

    print(tc_iiis_ranked)
