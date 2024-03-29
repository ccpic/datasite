from django.shortcuts import HttpResponse, render
from django.http import request
from .models import Negotiation, Subject
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, F, Q, QuerySet
from datetime import datetime
import pandas as pd

try:
    from io import BytesIO as IO  # for modern python
except ImportError:
    from io import StringIO as IO  # for legacy python


def get_filters(qs: QuerySet, field: str):
    all_records = (
        qs.values(field)
        .order_by(field)
        .annotate(count=Count(field))
        .filter(count__gt=0)  # 过滤掉计数为零的项
        .order_by(F("count").desc())
    )
    return all_records


def get_param(params):
    kw_param = params.get("kw")  # 根据空格拆分搜索关键字
    year_param = params.getlist("year")  # 年份
    tc1_param = params.getlist("tc1")  # tc1
    tc2_param = params.getlist("tc2")  # tc2
    ni_param = params.get("new_indication") # 适应症改变
    ne_param = params.get("no_exclusive") # 非独家品种

    # 下面部分准备所有高亮关键字
    highlights = {}
    try:
        kw_list = kw_param.split(" ")
    except Exception:
        kw_list = []

    for kw in kw_list:
        highlights[kw] = '<b class="highlight_kw">{}</b>'.format(kw)

    context = {
        "kw": kw_param,
        "years": [datetime.strptime(year, "%Y-%m-%d").date() for year in year_param],
        "tc1s": tc1_param,
        "tc2s": tc2_param,
        "new_indication": True if ni_param == "True" else None,
        "no_exclusive": True if ne_param == "True" else None,
        "highlights": highlights,
    }

    return context


DISPLAY_LENGTH = 10


@login_required
def subjects(request: request) -> HttpResponse:
    print(request.GET)
    param_dict = get_param(request.GET)

    subjects = Subject.objects.all()

    search_condition = Q()

    # 根据搜索筛选KOL
    kw = param_dict["kw"]

    if kw is not None:
        kw_list = kw.split(" ")
        for k in kw_list:
            search_condition.add(
                Q(name__icontains=k)  # 品种名称
                | Q(tc4__code__icontains=k)  # tc4 code
                | Q(tc4__name_cn__icontains=k)  # tc4 中文名
                | Q(tc4__name_en__icontains=k)  # tc4 英文名
                | Q(tc4__tc3__code__icontains=k)  # tc3 code
                | Q(tc4__tc3__name_cn__icontains=k)  # tc3 中文名
                | Q(tc4__tc3__name_en__icontains=k)  # tc3 英文名
                | Q(tc4__tc3__tc2__code__icontains=k)  # tc2 code
                | Q(tc4__tc3__tc2__name_cn__icontains=k)  # tc2 中文名
                | Q(tc4__tc3__tc2__name_en__icontains=k)  # tc2 英文名
                | Q(tc4__tc3__tc2__tc1__code__icontains=k)  # tc1 code
                | Q(tc4__tc3__tc2__tc1__name_cn__icontains=k)  # tc1 中文名
                | Q(tc4__tc3__tc2__tc1__name_en__icontains=k),  # tc1 英文名
                Q.AND,
            )

    # 根据年份筛选Record
    years = param_dict["years"]
    if years:
        search_condition.add(Q(subject_negotiations__nego_date__in=years), Q.AND)

    # 根据TC1筛选Record
    tc1s = param_dict["tc1s"]
    if tc1s:
        search_condition.add(Q(tc4__tc3__tc2__tc1__name_cn__in=tc1s), Q.AND)

    # 根据TC2筛选Record
    tc2s = param_dict["tc2s"]
    if tc2s:
        search_condition.add(Q(tc4__tc3__tc2__name_cn__in=tc2s), Q.AND)

    # 筛选适应症改变品种的Record
    new_indication = param_dict["new_indication"]
    if new_indication:
        search_condition.add(
            Q(subject_negotiations__new_indication=new_indication), Q.AND
        )
        
    # 筛选非独家品种
    no_exclusive= param_dict["no_exclusive"]
    if no_exclusive:
        search_condition.add(
            Q(subject_negotiations__is_exclusive=False), Q.AND
        )

    # 筛选并删除重复项
    search_result = subjects.filter(search_condition).distinct()

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
    sr_ids = [nego.id for nego in search_result]
    subjects = Subject.objects.filter(id__in=sr_ids).order_by("tc4__code", "name")

    paginator = Paginator(subjects, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    # 根据不同维度汇总记录数
    qs_years = get_filters(
        qs=subjects, field="subject_negotiations__nego_date"
    )  # 按年份汇总

    qs_years = qs_years.order_by("subject_negotiations__nego_date")  # 按年份从早到晚排序

    qs_tc1s = get_filters(qs=subjects, field="tc4__tc3__tc2__tc1__name_cn")  # 按TC1汇总

    qs_tc2s = get_filters(qs=subjects, field="tc4__tc3__tc2__name_cn")  # 按TC2汇总

    qs_new_indication = get_filters(
        qs=subjects, field="subject_negotiations__new_indication"
    )  # 按是否适应症改变

    qs_is_exclusive = get_filters(
        qs=subjects, field="subject_negotiations__is_exclusive"
    )  # 按是否独家品种

    context = {
        "subjects": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "kw": param_dict["kw"],
        # "highlights": param_dict["highlights"],
        "qs_years": qs_years,
        "selected_years": param_dict["years"],
        "qs_tc1s": qs_tc1s,
        "selected_tc1s": param_dict["tc1s"],
        "qs_tc2s": qs_tc2s,
        "selected_tc2s": param_dict["tc2s"],
        "qs_new_indication": qs_new_indication,
        "selected_new_indication": param_dict["new_indication"],
        "qs_is_exclusive": qs_is_exclusive,
        "selected_no_exclusive": param_dict["no_exclusive"],
    }

    return render(request, "nrdl_price/subjects.html", context)


@login_required()
def export(request):
    negos = Negotiation.objects.all()
    df = pd.DataFrame(
        list(
            negos.values(
                "subject__name",
                "subject__tc4__tc3__tc2__tc1__code",
                "subject__tc4__tc3__tc2__tc1__name_cn",
                "subject__tc4__tc3__tc2__code",
                "subject__tc4__tc3__tc2__name_cn",
                "subject__tc4__tc3__code",
                "subject__tc4__tc3__name_cn",
                "subject__tc4__code",
                "subject__tc4__name_cn",
                "nego_date",
                "reimbursement_start",
                "reimbursement_end",
                "nego_type",
                "new_indication",
                "is_exclusive",
                "price_new",
                "price_old",
                "dosage_for_price",
                "note",
            )
        )
    )

    df.columns = [
        "谈判品种名称",
        "TC I编码",
        "TC I名称",
        "TC II编码",
        "TC II名称",
        "TC III编码",
        "TC III名称",
        "TC IV编码",
        "TC IV名称",
        "谈判年份",
        "执行开始",
        "执行结束",
        "谈判类型",
        "是否更高适应症范围",
        "是否独家品种",
        "谈判后价格",
        "谈判前价格",
        "谈判价格对应剂型",
        "备注",
    ]

    df["谈判年份"] = pd.to_datetime(df["谈判年份"])
    df["谈判年份"] = df["谈判年份"].dt.year

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
    now = datetime.now().strftime("%Y%m%d%H%M%S")
    response["Content-Disposition"] = "attachment; filename=" + now + ".xlsx"
    return response
