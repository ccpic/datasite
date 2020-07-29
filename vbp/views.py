from .models import Tender, Volume, Bid, Company
from .serializers import TenderSerializer
from rest_framework import viewsets
from django.shortcuts import render, HttpResponse
from django.db.models import Q
import pandas as pd

try:
    from io import BytesIO as IO  # for modern python
except ImportError:
    from io import StringIO as IO  # for legacy python
import datetime

# class RecordViewSet(viewsets.ModelViewSet):
#     """
#     API - 带量采购记录
#     """
#     queryset = Record.objects.all().order_by('-pub_date')
#     serializer_class = RecordSerializer
#
#
# class TenderViewSet(viewsets.ModelViewSet):
#     """
#     API - 带量采购标的
#     """
#     queryset = Tender.objects.all()
#     serializer_class = TenderSerializer


def index(request):
    tenders = Tender.objects.all()

    context = {"tenders": tenders}
    return render(request, "vbp/tenders.html", context)


def analysis(request):
    tenders = Tender.objects.all()

    context = {"tenders": tenders}
    return render(request, "vbp/analysis.html", context)


def bid_detail(request, bid_id):
    bid = Bid.objects.get(pk=bid_id)

    context = {"bid": bid}
    return render(request, "vbp/bid_detail.html", context)


def tender_detail(request, tender_id):
    tender = Tender.objects.get(pk=tender_id)

    context = {"tender": tender}
    return render(request, "vbp/tender_detail.html", context)


def company_detail(request, record_id):
    company = Company.objects.get(pk=record_id)

    context = {"company": company}
    return render(request, "vbp/bid_detail.html", context)


def search(request):
    print(request.GET)
    kw = request.GET.get("kw")
    search_result = Tender.objects.filter(
        Q(target__icontains=kw)
        | Q(bids__bidder__full_name__icontains=kw)
        | Q(bids__bidder__abbr_name__icontains=kw)
    ).distinct()

    context = {"tenders": search_result, "kw": kw}

    return render(request, "vbp/tenders.html", context)


def export(request):
    tenders = pd.DataFrame(list(Tender.objects.all().values()))
    bids = pd.DataFrame(list(Bid.objects.all().values()))
    volumes = pd.DataFrame(list(Volume.objects.all().values()))
    companies =  pd.DataFrame(list(Company.objects.all().values()))
    tenders.rename(columns={"id": "tender_id"}, inplace=True)  # 修改列名，为之后merge匹配列做准备，下同
    df = pd.merge(volumes, tenders, how="left", on="tender_id")  # 以volume为base匹配tender
    bids.rename(columns={"id": "winner_id"}, inplace=True)
    df = pd.merge(df, bids, how="left", on="winner_id")  # 以volume+tender为base匹配bid
    companies.rename(columns={"id": "bidder_id"}, inplace=True)
    df = pd.merge(df, bids, how="left", on="winner_id")  # 以volume+tender+bid为base匹配company

    excel_file = IO()

    xlwriter = pd.ExcelWriter(excel_file, engine="xlsxwriter")

    df.to_excel(xlwriter, "data", index=True)

    xlwriter.save()
    xlwriter.close()

    excel_file.seek(0)

    # 设置浏览器mime类型
    response = HttpResponse(
        excel_file.read(),
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )

    # 设置文件名
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")  # 当前精确时间不会重复，适合用来命名默认导出文件
    response["Content-Disposition"] = "attachment; filename=" + now + ".xlsx"
    return response
