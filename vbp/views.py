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
        Q(target__icontains=kw)  # 搜索标的名称
        | Q(bids__bidder__full_name__icontains=kw)  # 搜索竞标公司全称
        | Q(bids__bidder__abbr_name__icontains=kw)  # 搜索竞标公司简称
        | Q(vol__icontains=kw)  # 搜索批次
    ).distinct()

    context = {"tenders": search_result, "kw": kw}

    return render(request, "vbp/tenders.html", context)


def export(request, mode, tender_ids):
    list_tender_ids = tender_ids.split("|")
    tender_objs = Tender.objects.filter(pk__in=list_tender_ids).distinct()
    bid_objs = Bid.objects.filter(tender__in=tender_objs).distinct()
    volume_objs = Volume.objects.filter(tender__in=tender_objs).distinct()
    company_objs = Company.objects.filter(bids__in=bid_objs).distinct()

    if mode == "volume":
        tenders = pd.DataFrame(list(tender_objs.values()))
        bids = pd.DataFrame(list(bid_objs.values()))
        volumes = pd.DataFrame(list(volume_objs.values()))
        companies = pd.DataFrame(list(company_objs.values()))

        tenders.rename(
            columns={"id": "tender_id"}, inplace=True
        )  # 修改列名，为之后merge匹配列做准备，下同
        df = pd.merge(
            volumes, tenders, how="left", on="tender_id"
        )  # 以volume为base匹配tender

        bids.rename(columns={"id": "winner_id"}, inplace=True)
        df = pd.merge(df, bids, how="left", on="winner_id")  # 以volume+tender为base匹配bid

        companies.rename(columns={"id": "bidder_id"}, inplace=True)
        df = pd.merge(
            df, companies, how="left", on="bidder_id"
        )  # 以volume+tender+bid为base匹配company

        df = df[
            [
                "vol",
                "target",
                "spec",
                "tender_begin",
                "ceiling_price",
                "region",
                "amount_contract",
                "full_name",
                "abbr_name",
                "mnc_or_local",
                "origin",
                "bid_price",
                "original_price",
            ]
        ]

        df.columns = [
            "批次",
            "标的",
            "剂型剂量",
            "标期开始时间",
            "最高有效申报价",
            "地区",
            "合同量",
            "竞标公司全称",
            "竞标公司简称",
            "是否跨国公司",
            "是否此标的原研",
            "竞标价",
            "集采前价格",
        ]
    elif mode == "tender":
        tenders = pd.DataFrame(list(tender_objs.values()))
        bids = pd.DataFrame(list(bid_objs.values()))
        companies = pd.DataFrame(list(company_objs.values()))

        companies.rename(columns={"id": "bidder_id"}, inplace=True)
        df = pd.merge(bids, companies, how="left", on="bidder_id")  # 以bid为base匹配company

        tenders.rename(columns={"id": "tender_id"}, inplace=True)
        df = pd.merge(
            df, tenders, how="left", on="tender_id"
        )  # 以bid+company为base匹配tender

        df["is_winner"] = df.apply(
            lambda x: Bid.objects.get(pk=x["id"]).is_winner(), axis=1
        )  # 添加列：是否中标
        df["specs"] = df.apply(
            lambda x: ",".join(list(Tender.objects.get(pk=x["tender_id"]).get_specs())),
            axis=1,
        )  # 添加列：剂型剂量
        df["regions_win"] = df.apply(
            lambda x: ",".join(list(Bid.objects.get(pk=x["id"]).regions_win())), axis=1,
        )  # 添加中标区域
        df = df[
            [
                "vol",
                "target",
                "specs",
                "tender_begin",
                "ceiling_price",
                "full_name",
                "abbr_name",
                "mnc_or_local",
                "origin",
                "bid_price",
                "original_price",
                "is_winner",
                "regions_win",
            ]
        ]

        df.columns = [
            "批次",
            "标的",
            "标的剂型剂量",
            "标期开始时间",
            "最高有效申报价",
            "竞标公司全称",
            "竞标公司简称",
            "是否跨国公司",
            "是否此标的原研",
            "竞标价",
            "集采前价格",
            "是否中标",
            "中标区域",
        ]
    excel_file = IO()

    xlwriter = pd.ExcelWriter(excel_file, engine="xlsxwriter")

    df.to_excel(xlwriter, "data", index=False)

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
