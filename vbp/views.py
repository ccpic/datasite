from .models import Tender, Volume, Bid, Company, Doc
from django.contrib.auth.decorators import login_required
from .serializers import TenderSerializer
from rest_framework import viewsets
from django.shortcuts import render, HttpResponse
from django.db.models import Q
import pandas as pd
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
import random

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


DISPLAY_LENGTH = 10

HOT_KWS = [
    "扩围",
    "第二轮",
    "第三轮",
    "第四轮",
    "第五轮",
    "信立泰",
    "氯吡格雷",
    "奥美沙坦",
    "替格瑞洛",
    "地氯雷他定",
    "匹伐他汀",
    "比伐芦定",
    "贝那普利",
    "乐卡地平",
    "利伐沙班",
    "头孢呋辛",
]


@login_required
def index(request):
    tenders = Tender.objects.all()
    paginator = Paginator(tenders, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    context = {
        "tenders": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "hot_kws": HOT_KWS,
    }
    return render(request, "vbp/tenders.html", context)


@login_required
def analysis(request):
    tenders = Tender.objects.all()

    context = {"tenders": tenders}
    return render(request, "vbp/analysis.html", context)


@login_required
def docs(request):
    docs = Doc.objects.all()

    context = {"docs": docs}
    return render(request, "vbp/docs.html", context)


@login_required
def bid_detail(request, bid_id):
    bid = Bid.objects.get(pk=bid_id)

    context = {"bid": bid}
    return render(request, "vbp/bid_detail.html", context)


@login_required
def tender_detail(request, tender_id):
    tender = Tender.objects.get(pk=tender_id)

    context = {"tender": tender}
    return render(request, "vbp/tender_detail.html", context)


@login_required
def company_detail(request, record_id):
    company = Company.objects.get(pk=record_id)

    context = {"company": company}
    return render(request, "vbp/bid_detail.html", context)


@login_required
def search(request):
    print(request.GET)
    kw = request.GET.get("kw")
    search_result = Tender.objects.filter(
        Q(target__icontains=kw)  # 搜索标的名称
        | Q(bids__bidder__full_name__icontains=kw)  # 搜索竞标公司全称
        | Q(bids__bidder__abbr_name__icontains=kw)  # 搜索竞标公司简称
        | Q(vol__icontains=kw)  # 搜索批次
    ).distinct()

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinc(),order_by()等queryset时出现重复对象的bug
    sr_ids = [tender.id for tender in search_result]
    search_result2 = Tender.objects.filter(id__in=sr_ids)

    paginator = Paginator(
        search_result2, DISPLAY_LENGTH
    )  #  为了克服pagination bug这里的参数时search_result2
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    context = {
        "tenders": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "kw": kw,
        "hot_kws": HOT_KWS,
    }

    return render(request, "vbp/tenders.html", context)


@login_required
def export(request, mode, tender_ids=None):
    if tender_ids is None:
        tender_objs = Tender.objects.all()
        bid_objs = Bid.objects.all()
        volume_objs = Volume.objects.all()
        company_objs = Company.objects.all()
    else:
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

        # df["proc_percentage"] = df.apply(
        #     lambda x: Tender.objects.get(pk=x["tender_id"]).proc_percentage, axis=1
        # )  # 添加列：集采比例
        df["amount_contract"] = df.apply(
            lambda x: Volume.objects.get(pk=x["id"]).amount_contract(), axis=1
        )  # 添加列：实际合同量

        df = df[
            [
                "vol",
                "target",
                "spec",
                "tender_begin",
                "ceiling_price",
                "region",
                "amount_reported",
                # "proc_percentage",
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
            "区域报量",
            # "集采比例",
            "实际合同量",
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
        df["total_std_volume_reported"] = df.apply(
            lambda x: Tender.objects.get(pk=x["tender_id"]).total_std_volume_reported(),
            axis=1,
        )  # 添加列：标的官方报量
        df["total_std_volume_contract"] = df.apply(
            lambda x: Tender.objects.get(pk=x["tender_id"]).total_std_volume_contract(),
            axis=1,
        )  # 添加列：标的实际合同量
        df["total_value_contract"] = df.apply(
            lambda x: Tender.objects.get(pk=x["tender_id"]).total_value_contract(),
            axis=1,
        )  # 添加列：标的实际合同金额
        df["specs"] = df.apply(
            lambda x: ",".join(list(Tender.objects.get(pk=x["tender_id"]).get_specs())),
            axis=1,
        )  # 添加列：剂型剂量
        df["regions_win"] = df.apply(
            lambda x: ",".join(list(Bid.objects.get(pk=x["id"]).regions_win())), axis=1,
        )  # 添加中标区域
        df["std_volume_win"] = df.apply(
            lambda x: Bid.objects.get(pk=x["id"]).std_volume_win(), axis=1
        )  # 添加列：竞标者赢得实际合同量
        df["value_win"] = df.apply(
            lambda x: Bid.objects.get(pk=x["id"]).value_win(), axis=1
        )  # 添加列：竞标者赢得实际合同金额
        df["tender_period"] = df.apply(
            lambda x: Tender.objects.get(pk=x["tender_id"]).tender_period, axis=1
        )  # 添加列：标期
        df["proc_percentage"] = df.apply(
            lambda x: Tender.objects.get(pk=x["tender_id"]).proc_percentage, axis=1
        )  # 添加列：带量比例

        df = df[
            [
                "vol",
                "target",
                "specs",
                "tender_begin",
                "tender_period",
                "ceiling_price",
                "total_std_volume_reported",
                "proc_percentage",
                "total_std_volume_contract",
                "total_value_contract",
                "full_name",
                "abbr_name",
                "mnc_or_local",
                "origin",
                "bid_price",
                "original_price",
                "is_winner",
                "std_volume_win",
                "value_win",
                "regions_win",
            ]
        ]

        df.columns = [
            "批次",
            "标的",
            "标的剂型剂量",
            "标期开始时间",
            "标期",
            "最高有效申报价",
            "标的官方报量",
            "标的带量比例",
            "标的实际合同量",
            "标的实际合同金额",
            "竞标公司全称",
            "竞标公司简称",
            "是否跨国公司",
            "是否此标的原研",
            "竞标价",
            "集采前价格",
            "是否中标",
            "竞标者赢得实际合同量",
            "竞标者赢得实际合同金额",
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
