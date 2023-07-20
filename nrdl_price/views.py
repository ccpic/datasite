from django.shortcuts import HttpResponse, redirect, render, reverse
from django.http import request
from .models import Negotiation
from django.contrib.auth.decorators import login_required
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db.models import Count, F, Q, QuerySet

def get_param(params):
    kw_param = params.get("kw")  # 根据空格拆分搜索关键字
    kol_param = params.get("kol")
    prov_param = params.getlist("province")  # 省份可能多选，需要额外处理
    city_param = params.getlist("city")  # 省份可能多选，需要额外处理
    month_param = params.getlist("month")

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

    context = {
        "kw": kw_param,
        "kol": kol_param,
        "provinces": prov_param,
        "cities": city_param,
        "months": month_param,
        # "nations": nation_id_list,
        # "program": prog_param,
        "highlights": highlights,
    }

    return context

DISPLAY_LENGTH = 10

@login_required
def negos(request: request) -> HttpResponse:
    print(request.GET)
    param_dict = get_param(request.GET)

    negos = Negotiation.objects.all()
    
    search_condition = Q()

    # # 根据搜索筛选KOL
    # kw = param_dict["kw"]
    # if kw is not None:
    #     kw_list = kw.split(" ")
    #     for k in kw_list:
    #         search_condition.add(
    #             Q(kol__name__icontains=k)  # 搜索KOL姓名
    #             | Q(kol__hospital__name__icontains=k)  # 搜索供职医院名称
    #             | Q(purpose__icontains=k)  # 搜索拜访目标
    #             | Q(feedback__icontains=k),  # 搜索主要反馈
    #             Q.AND,
    #         )

    # # 根据省份筛选Record
    # provinces = param_dict["provinces"]
    # if provinces:
    #     search_condition.add(Q(kol__hospital__province__in=provinces), Q.AND)

    # # 根据城市筛选Record
    # cities = param_dict["cities"]
    # if cities:
    #     search_condition.add(Q(kol__hospital__city__in=cities), Q.AND)

    # # 根据月份筛选Record
    # months = param_dict["months"]
    # if months:
    #     search_condition_month = Q()
    #     for k in months:
    #         visit_date = datetime.datetime.strptime(k, "%Y-%m-%d").date()
    #         visit_year = visit_date.year
    #         visit_month = visit_date.month
    #         search_condition_month.add(
    #             Q(visit_date__year=visit_year, visit_date__month=visit_month), Q.OR
    #         )
    #     search_condition.add(search_condition_month, Q.AND)

    # # 根据Kol筛选Record
    # kol = param_dict["kol"]
    # if kol:
    #     search_condition.add(Q(kol__pk=kol), Q.AND)

    # 筛选并删除重复项
    search_result = negos.filter(search_condition).distinct()

    #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
    sr_ids = [nego.id for nego in search_result]
    negos = Negotiation.objects.filter(id__in=sr_ids).order_by("subject__name")

    paginator = Paginator(negos, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    # # 根据不同维度汇总记录数
    # filtered_provinces = get_filters(
    #     qs=records_by_auth(request.user), field="kol__hospital__province"
    # )  # 按省份汇总
    # filtered_cities = get_filters(
    #     qs=records_by_auth(request.user), field="kol__hospital__city"
    # )  # 按城市汇总
    # filtered_months = (
    #     records_by_auth(request.user)
    #     .annotate(month=TruncMonth("visit_date"))
    #     .values("month")
    #     .annotate(count=Count("id"))
    #     .order_by(F("month").desc())
    # )  # 按拜访月份汇总

    context = {
        "negos": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        # "kw": param_dict["kw"],
        # "kol": Kol.objects.get(pk=int(param_dict["kol"])) if kol else None,
        # "highlights": param_dict["highlights"],
        # "filtered_provinces": filtered_provinces,
        # "selected_provinces": param_dict["provinces"],
        # "filtered_cities": filtered_cities,
        # "selected_cities": param_dict["cities"],
        # "filtered_months": filtered_months,
        # "selected_months": param_dict["months"],
    }

    return render(request, "nrdl_price/negos.html", context)
