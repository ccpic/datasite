from django.shortcuts import render
from .models import Company, Drug, Sales, CURRENT_YEAR
from django.contrib.auth.decorators import login_required


@login_required
def index(request):
    companies = Company.objects.all()
    companies_ranked = sorted(
        companies, key=lambda x: x.annual_netsales, reverse=True
    )  # 按最新年份销售由高到低排序
    sales_ranked = Sales.objects.filter(year=CURRENT_YEAR).order_by("-netsales_value")
    # drugs_ranked = sorted(drugs, key=lambda x: x.annual_netsales, reverse=True) # 按最新年份销售由高到低排序
    context = {
        "companies_ranked": companies_ranked,
        "sales_ranked": sales_ranked,
    }
    return render(request, "rdpac/index.html", context)


@login_required
def drug_detail(request, pk):
    drug = Drug.objects.get(pk=pk)
    sales = drug.sales.all()
    context = {
        "drug": drug,
        "sales": sales,
    }
    return render(request, "rdpac/drug_detail.html", context)