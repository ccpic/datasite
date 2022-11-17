import pandas as pd
from django.shortcuts import render, HttpResponse, redirect, reverse
from django.http import request
from django.contrib.auth.decorators import login_required
import json
from .models import Hospital, Kol, Record
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datasite.commons import get_dt_page
from django.db.models import Q, F, Count
from django.db import IntegrityError

DISPLAY_LENGTH = 20


def get_filters(model, field: str):
    all_provinces = (
        model.objects.all()
        .values(field)
        .order_by(field)
        .annotate(count=Count(field))
        .order_by(F("count").desc())
    )
    return all_provinces


def get_param(params):
    kw_param = params.get("kw")  # 根据空格拆分搜索关键字

    prov_param = params.getlist("province")  # 省份可能多选，需要额外处理

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
        "provinces": prov_param,
        # "nations": nation_id_list,
        # "program": prog_param,
        "highlights": highlights,
    }

    return context


@login_required
def records(request: request) -> HttpResponse:
    print(request.GET)
    param_dict = get_param(request.GET)

    records = Record.objects.all()

    # # 根据搜索筛选文章
    # kw = param_dict["kw"]
    # if kw is not None:
    #     kw_list = kw.split(" ")

    #     search_condition = Q(name__icontains=kw_list[0]) | Q(  # 搜索KOL姓名
    #         hospital__name__icontains=kw_list[0]
    #     )  # 搜索供职医院名称
    #     for k in kw_list[1:]:
    #         search_condition.add(
    #             Q(name__icontains=k)  # 搜索KOL姓名
    #             | Q(hospital__name__icontains=k),  # 搜索供职医院名称
    #             Q.AND,
    #         )

    #     search_result = kols.filter(search_condition).distinct()

    #     #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
    #     sr_ids = [kol.id for kol in search_result]
    #     kols = Kol.objects.filter(id__in=sr_ids)

    paginator = Paginator(records, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    context = {
        "records": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "kw": param_dict["kw"],
    }

    return render(request, "kol/records.html", context)


@login_required
def create_record(request):
    print(request.POST)
    if request.method == "POST":
        obj = Kol(
            name=request.POST.get("name"),
            hospital=Hospital.objects.get(pk=int(request.POST.get("select_hp"))),
            dept=request.POST.get("dept"),
            rating_infl=int(request.POST.get("rating_infl")),
            rating_prof=int(request.POST.get("rating_prof")),
            titles=request.POST.get("text_title"),
            pub_user=request.user,
        )
        try:
            obj.save()
        except IntegrityError:
            context = {"kol": obj}
            return render(request, "kol/kol_duplicated.html", context)

        return redirect(reverse("kol:records"))
    else:
        kols = Kol.objects.all()
        context = {
            "kols": kols,
            "all_provinces": get_filters(model=Record, field="kol__hospital__province"),
        }
        return render(request, "kol/create_record.html", context)


@login_required
def kols(request: request) -> HttpResponse:
    print(request.GET)
    param_dict = get_param(request.GET)

    kols = Kol.objects.all().order_by("name")

    # 根据搜索筛选KOL
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
        kols = Kol.objects.filter(id__in=sr_ids).order_by("name")

    # 根据省份筛选Kol
    provinces = param_dict["provinces"]
    if provinces:
        kols = kols.filter(hospital__province__in=provinces)

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
        "all_provinces": get_filters(model=Kol, field="hospital__province"),
        "selected_provinces": param_dict["provinces"],
    }

    return render(request, "kol/kols.html", context)


@login_required
def create_kol(request):
    print(request.POST)
    if request.method == "POST":
        obj = Kol(
            name=request.POST.get("name"),
            hospital=Hospital.objects.get(pk=int(request.POST.get("select_hp"))),
            dept=request.POST.get("dept"),
            rating_infl=int(request.POST.get("rating_infl")),
            rating_prof=int(request.POST.get("rating_prof")),
            titles=request.POST.get("text_title"),
            pub_user=request.user,
        )
        try:
            obj.save()
        except IntegrityError:
            context = {"kol": obj}
            return render(request, "kol/kol_duplicated.html", context)

        return redirect(reverse("kol:kols"))
    else:
        hospitals = Hospital.objects.all()
        context = {
            "hospitals": hospitals,
            "all_provinces": get_filters(model=Kol, field="hospital__province"),
        }
        return render(request, "kol/create_kol.html", context)


@login_required
def update_kol(request, pk: int):
    print(request.POST)
    if request.method == "POST":
        obj = Kol.objects.get(pk=pk)
        obj.name = request.POST.get("name")
        obj.hospital = Hospital.objects.get(pk=int(request.POST.get("select_hp")))
        obj.dept = request.POST.get("dept")
        obj.rating_infl = int(request.POST.get("rating_infl"))
        obj.rating_prof = int(request.POST.get("rating_prof"))
        obj.titles = request.POST.get("text_title")
        obj.pub_user = request.user

        try:
            obj.save()
        except IntegrityError:
            context = {"kol": obj}
            return render(request, "kol/kol_duplicated.html", context)

        return redirect(reverse("kol:kols"))
    else:
        hospitals = Hospital.objects.all()
        context = {
            "kol": Kol.objects.get(pk=pk),
            "hospitals": hospitals,
            "all_provinces": get_filters(model=Kol, field="hospital__province"),
        }
        return render(request, "kol/update_kol.html", context)


@login_required
def delete_kol(request):
    print(request.POST)
    if request.method == "POST":
        id = request.POST.get("id")
        qs_to_delete = Kol.objects.get(id=id)  # 执行删除操作
        qs_to_delete.delete()
        return redirect(reverse("kol:kols"))


def bad_request(message):
    response = HttpResponse(
        json.dumps({"message": message}), content_type="application/json"
    )
    response.status_code = 400
    return response
