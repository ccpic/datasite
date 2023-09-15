from django.shortcuts import HttpResponse, redirect, render, reverse
from django.http import request
from .models import Subject, Subject
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Case, When, Value, Count, CharField, F, Q, QuerySet
from datetime import datetime


def get_filters(qs: QuerySet, field: str):
    print(qs.values(field))
    all_records = (
        qs.values(field)
        .order_by(field)
        .annotate(count=Count(field))
        .order_by(F("count").desc())
    )
    return all_records


def get_param(params):
    kw_param = params.get("kw")  # 根据空格拆分搜索关键字
    year_param = params.getlist("year")  # 年份
    tc1_param = params.getlist("tc1")  # tc1
    tc2_param = params.getlist("tc2")  # tc2

    # 下面部分准备所有高亮关键字
    highlights = {}
    try:
        kw_list = kw_param.split(" ")
    except:
        kw_list = []

    for kw in kw_list:
        highlights[kw] = '<b class="highlight_kw">{}</b>'.format(kw)

    context = {
        "kw": kw_param,
        "years": [datetime.strptime(year, "%Y-%m-%d").date() for year in year_param],
        "tc1s": tc1_param,
        "tc2s": tc2_param,
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

    # 筛选并删除重复项
    search_result = subjects.filter(search_condition).distinct()

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
    sr_ids = [nego.id for nego in search_result]
    subjects = Subject.objects.filter(id__in=sr_ids).order_by("name")

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
    }

    return render(request, "nrdl_price/subjects.html", context)
