from django.shortcuts import render
import pandas as pd
from .models import Announce
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.db.models import Q, F, Count, Min


DISPLAY_LENGTH = 20


def get_id_list(param):
    id_list = []
    for id in param:
        if isinstance(id, int) == int:
            id_list.append(id)
        else:
            id_list.append(int(id))

    return id_list


def get_param(params):
    kw_param = params.get("kw")  # 根据空格拆分搜索关键字

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
        "sources": params.getlist("source"),  # source可能多选
        "regions": params.getlist("region"),  # region可能多选
        "highlights": highlights,
    }

    return context


# 首页
@login_required
def feeds(request):
    print(request.GET)
    param_dict = get_param(request.GET)

    # 所有公告
    announces = Announce.objects.all()

    # 根据搜索筛选公告
    kw = param_dict["kw"]
    if kw is not None:
        kw_list = kw.split(" ")

        search_condition = Q(title__icontains=kw_list[0]) | Q(  # 搜索公告标题
            source__icontains=kw_list[0]
        )  # 搜索公告来源
        for k in kw_list[1:]:
            search_condition.add(
                Q(title__icontains=k) | Q(source__icontains=k),  # 搜索公告标题  # 搜索公告来源
                Q.AND,
            )

        announces = announces.filter(search_condition).distinct()

        # #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
        # sr_ids = [announce.id for announce in search_result]
        # announces = Announce.objects.filter(id__in=sr_ids)

    # 筛选区域，多源之间是或的关系
    regions = param_dict["regions"]
    if regions is not None and len(regions) != 0:
        region_condition = Q(region=regions[0])
        for region in regions[1:]:
            region_condition.add(Q(region=region), Q.OR)
        announces = announces.filter(region_condition).distinct()

        # #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
        # sr_ids = [announce.id for announce in region_result]
        # announces = Announce.objects.filter(id__in=sr_ids)

    # 筛选公告源，多源之间是或的关系
    sources = param_dict["sources"]
    if sources is not None and len(sources) != 0:
        source_condition = Q(source=sources[0])
        for source in sources[1:]:
            source_condition.add(Q(source=source), Q.OR)
        announces = announces.filter(source_condition).distinct()

        # #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
        # sr_ids = [announce.id for announce in source_result]
        # announces = Announce.objects.filter(id__in=sr_ids)
        
    # 爬取时间，取最早值
    fetch_date = Announce.objects.all().aggregate(Min("fetch_date"))

    # 分页
    paginator = Paginator(announces, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    all_sources = (
        Announce.objects.order_by("source").values_list("source", flat=True).distinct()
    )  # 所有公告源
    filter_sources = (
        announces.order_by("source").values_list("source", flat=True).distinct()
    )  # 筛选出所有关联公告的源
    
    all_regions = (
        Announce.objects.order_by("region").values_list("region", flat=True).distinct()
    )  # 所有公告源
    filter_regions = (
        announces.order_by("region").values_list("region", flat=True).distinct()
    )  # 筛选出所有关联公告的源
    
    context = {
        "announces": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "kw": param_dict["kw"],
        "highlights": param_dict["highlights"],
        "all_sources": all_sources,
        "filter_sources": filter_sources,
        "sources_selected": param_dict["sources"],
        "all_regions": all_regions,
        "filter_regions": filter_regions,
        "regions_selected": param_dict["regions"],
        "fetch_date": fetch_date,
    }
    return render(request, "policy_feed/feeds.html", context)

