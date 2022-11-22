import pandas as pd
from django.shortcuts import render, HttpResponse, redirect, reverse
from django.http import request
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
import json
from .models import Hospital, Kol, Record, Attachment
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from datasite.commons import get_dt_page
from django.db.models import Q, F, Count, QuerySet
from django.db import IntegrityError
from django.db.models.functions import TruncMonth
import datetime

DISPLAY_LENGTH = 8


def records_by_auth(user:User):
    if user.is_staff:
        return Record.objects.all()
    else:
        return Record.objects.filter(pub_user=user)

def kols_by_auth(user:User):
    if user.groups.filter(name="KOL信息贡献者").exists():
        return Kol.objects.all().order_by("name")
    else:
        return Kol.objects.none()

def get_filters(qs: QuerySet, field: str):
    all_provinces = (
        qs.values(field)
        .order_by(field)
        .annotate(count=Count(field))
        .order_by(F("count").desc())
    )
    return all_provinces


def get_param(params):
    kw_param = params.get("kw")  # 根据空格拆分搜索关键字
    kol_param = params.get("kol")
    prov_param = params.getlist("province")  # 省份可能多选，需要额外处理
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
        "months": month_param,
        # "nations": nation_id_list,
        # "program": prog_param,
        "highlights": highlights,
    }

    return context


@login_required
def records(request: request) -> HttpResponse:
    print(request.GET)
    param_dict = get_param(request.GET)

    # 如果是管理员，显示全部记录，否则仅显示当前用户上传的记录
    records = records_by_auth(request.user)

    # 根据搜索筛选KOL
    kw = param_dict["kw"]
    if kw is not None:
        kw_list = kw.split(" ")

        search_condition = (
            Q(kol__name__icontains=kw_list[0])  # 搜索KOL姓名
            | Q(kol__hospital__name__icontains=kw_list[0])  # 搜索供职医院名称
            | Q(purpose__icontains=kw_list[0])  # 搜索拜访目标
            | Q(feedback_main__icontains=kw_list[0])  # 搜索主要反馈
            | Q(feedback_oth__icontains=kw_list[0])  # 搜索其他重要信息
        )
        for k in kw_list[1:]:
            search_condition.add(
                Q(kol__name__icontains=k)  # 搜索KOL姓名
                | Q(kol__hospital__name__icontains=k)  # 搜索供职医院名称
                | Q(purpose__icontains=k)  # 搜索拜访目标
                | Q(feedback_main__icontains=k)  # 搜索主要反馈
                | Q(feedback_oth__icontains=k),  # 搜索其他重要信息
                Q.AND,
            )

        search_result = records.filter(search_condition).distinct()

        #  下方两行代码为了克服MSSQL数据库和Django pagination在distinct(),order_by()等queryset时出现重复对象的bug
        sr_ids = [record.id for record in search_result]
        records = Record.objects.filter(id__in=sr_ids).order_by("-visit_date")

    # 根据Kol筛选Record
    kol = param_dict["kol"]
    if kol:
        records = records.filter(kol__pk=kol)

    # 根据省份筛选Record
    provinces = param_dict["provinces"]
    if provinces:
        records = records.filter(kol__hospital__province__in=provinces)

    # 根据月份筛选Record
    months = param_dict["months"]
    if months:
        visit_date = datetime.datetime.strptime(months[0], "%Y-%m-%d").date()
        visit_year = visit_date.year
        visit_month = visit_date.month
        records_temp = records.filter(
            visit_date__year=visit_year, visit_date__month=visit_month
        )
        for k in months[1:]:
            visit_date = datetime.datetime.strptime(k, "%Y-%m-%d").date()
            visit_year = visit_date.year
            visit_month = visit_date.month
            records_temp = records_temp | records.filter(
                visit_date__year=visit_year, visit_date__month=visit_month
            )

        records = records_temp

    paginator = Paginator(records, DISPLAY_LENGTH)
    page = request.GET.get("page")

    try:
        rows = paginator.page(page)
    except PageNotAnInteger:
        rows = paginator.page(1)
    except EmptyPage:
        rows = paginator.page(paginator.num_pages)

    # 根据不同维度汇总记录数
    filtered_provinces = get_filters(
        qs=records_by_auth(request.user), field="kol__hospital__province"
    )  # 按省份汇总
    filtered_months = (
        records_by_auth(request.user)
        .annotate(month=TruncMonth("visit_date"))
        .values("month")
        .annotate(count=Count("id"))
        .order_by(F("month").desc())
    )  # 按拜访月份汇总

    context = {
        "records": rows,
        "num_pages": paginator.num_pages,
        "record_n": paginator.count,
        "display_length": DISPLAY_LENGTH,
        "kw": param_dict["kw"],
        "kol": Kol.objects.get(pk=int(param_dict["kol"])) if kol else None,
        "highlights": param_dict["highlights"],
        "filtered_provinces": filtered_provinces,
        "selected_provinces": param_dict["provinces"],
        "filtered_months": filtered_months,
        "selected_months": param_dict["months"],
    }

    return render(request, "kol/records.html", context)


@login_required
def create_record(request):
    print(request.POST)
    if request.method == "POST":
        obj = Record(
            kol=Kol.objects.get(pk=int(request.POST.get("select_kol"))),
            visit_date=datetime.datetime.strptime(
                request.POST.get("visit_date"), "%Y-%m-%d"
            ).date(),
            purpose=request.POST.get("text_purpose"),
            rating_awareness=int(request.POST.get("rating_awareness")),
            rating_efficacy=int(request.POST.get("rating_efficacy")),
            rating_safety=int(request.POST.get("rating_safety")),
            rating_compliance=int(request.POST.get("rating_compliance")),
            feedback=request.POST.get("text_feedback"),
            pub_user=request.user,
        )
        obj.save()

        return redirect(reverse("kol:records"))
    else:
        kols = Kol.objects.all()
        # 根据不同维度汇总记录数
        filtered_provinces = get_filters(
            qs=records_by_auth(request.user), field="kol__hospital__province"
        )  # 按省份汇总
        filtered_months = (
            records_by_auth(request.user)
            .annotate(month=TruncMonth("visit_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by(F("month").desc())
        )  # 按拜访月份汇总
        context = {
            "rating_awareness_choices": Record.RATING_AWARENESS_CHOICES,
            "rating_efficacy_choices": Record.RATING_EFFICACY_CHOICES,
            "rating_safety_choices": Record.RATING_SAFETY_CHOICES,
            "rating_compliance_choices": Record.RATING_COMPLIANCE_CHOICES,
            "kols": kols,
            "filtered_provinces": filtered_provinces,
            "filtered_months": filtered_months,
        }
        return render(request, "kol/create_record.html", context)


@login_required
def update_record(request, pk: int):
    print(request.POST, request.FILES)
    if request.method == "POST":
        obj = Record.objects.get(pk=pk)
        obj.kol = Kol.objects.get(pk=int(request.POST.get("select_kol")))
        obj.visit_date = datetime.datetime.strptime(
            request.POST.get("visit_date"), "%Y-%m-%d"
        ).date()
        obj.purpose = request.POST.get("text_purpose")
        obj.rating_awareness = int(request.POST.get("rating_awareness"))
        obj.rating_efficacy = int(request.POST.get("rating_efficacy"))
        obj.rating_safety = int(request.POST.get("rating_safety"))
        obj.rating_compliance = int(request.POST.get("rating_compliance"))
        obj.feedback = request.POST.get("text_feedback")
        obj.pub_user = request.user
        obj.save()

        # for file in request.FILES:
        #     obj_attachment = Attachment(record=obj, file=file)
        #     obj_attachment.save()

        return redirect(reverse("kol:records"))
    else:
        kols = Kol.objects.all()
        # 根据不同维度汇总记录数
        filtered_provinces = get_filters(
            qs=records_by_auth(request.user), field="kol__hospital__province"
        )  # 按省份汇总
        filtered_months = (
            records_by_auth(request.user)
            .annotate(month=TruncMonth("visit_date"))
            .values("month")
            .annotate(count=Count("id"))
            .order_by(F("month").desc())
        )  # 按拜访月份汇总
        context = {
            "rating_awareness_choices": Record.RATING_AWARENESS_CHOICES,
            "rating_efficacy_choices": Record.RATING_EFFICACY_CHOICES,
            "rating_safety_choices": Record.RATING_SAFETY_CHOICES,
            "rating_compliance_choices": Record.RATING_COMPLIANCE_CHOICES,
            "record": Record.objects.get(pk=pk),
            "attachments": Attachment.objects.filter(record=Record.objects.get(pk=pk)),
            "kols": kols,
            "filtered_provinces": filtered_provinces,
            "filtered_months": filtered_months,
        }
        return render(request, "kol/create_record.html", context)


@login_required
def delete_record(request):
    print(request.POST)
    if request.method == "POST":
        id = request.POST.get("id")
        qs_to_delete = Record.objects.get(id=id)  # 执行删除操作
        qs_to_delete.delete()
        return redirect(reverse("kol:records"))


@login_required
def kols(request: request) -> HttpResponse:
    print(request.GET)
    param_dict = get_param(request.GET)

    kols = kols_by_auth(request.user)

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
        "filtered_provinces": get_filters(
            qs=kols_by_auth(request.user), field="hospital__province"
        ),
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
            "filtered_provinces": get_filters(
                qs=kols_by_auth(request.user), field="hospital__province"
            ),
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
            "kol": kols_by_auth(request.user).get(pk=pk),
            "hospitals": hospitals,
            "filtered_provinces": get_filters(
                qs=kols_by_auth(request.user), field="hospital__province"
            ),
        }
        return render(request, "kol/create_kol.html", context)


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

