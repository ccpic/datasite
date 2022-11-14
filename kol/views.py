import pandas as pd
from django.shortcuts import render, HttpResponse
from django.http import request
from django.contrib.auth.decorators import login_required
import json
from .models import Hospital, Kol
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datasite.commons import get_dt_page
from django.db.models import Q, F, Count

DISPLAY_LENGTH = 20


def get_param(params):
    kw_param = params.get("kw")  # 根据空格拆分搜索关键字

    # tag_param = params.getlist("tag")  # tag可能多选，需要额外处理
    # tag_id_list = get_id_list(tag_param)

    # nation_param = params.getlist("nation")  # 国家参数
    # nation_id_list = get_id_list(nation_param)

    # prog_param = params.get("program")  # 栏目参数

    # 下面部分准备所有高亮关键字
    highlights = {}
    try:
        kw_list = kw_param.split(" ")
    except:
        kw_list = []

    for kw in kw_list:
        highlights[kw] = '<b class="highlight_kw">{}</b>'.format(kw)

    # for tag_id in tag_id_list:
    #     tag = Tag.objects.get(pk=tag_id)
    #     highlights[tag.name] = '<b class="highlight_tag">{}</b>'.format(tag.name)

    context = {
        "kw": kw_param,
        # "tags": tag_id_list,
        # "nations": nation_id_list,
        # "program": prog_param,
        "highlights": highlights,
    }

    return context


@login_required
def kols(request: request) -> HttpResponse:
    print(request.GET)
    param_dict = get_param(request.GET)

    kols = Kol.objects.all()

    # 根据搜索筛选文章
    kw = param_dict["kw"]
    if kw is not None:
        kw_list = kw.split(" ")

        search_condition = Q(name__icontains=kw_list[0]) | Q(  # 搜索KOL姓名
            hospital__name__icontains=kw_list[0]
        )  # 搜索供职医院名称
        for k in kw_list[1:]:
            search_condition.add(
                Q(name__icontains=k)  # 搜索KOL姓名
                | Q(hospital__name__icontains=k),  # 搜索供职医院名称
                Q.AND,
            )

        search_result = kols.filter(search_condition).distinct()

        #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
        sr_ids = [kol.id for kol in search_result]
        kols = Kol.objects.filter(id__in=sr_ids)

    paginator = Paginator(kols, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    context = {
        "kols": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "kw": param_dict["kw"],
    }

    return render(request, "kol/kols.html", context)
