import datetime
import json

import pandas as pd
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import EmptyPage, PageNotAnInteger, Paginator
from django.db import IntegrityError
from django.db.models import Count, F, Q, QuerySet
from django.db.models.functions import TruncMonth
from django.http import request
from django.shortcuts import HttpResponse, redirect, render, reverse
from django.utils import timezone

from datasite.commons import get_dt_page

from .models import *

try:
    from io import BytesIO as IO  # for modern python
except ImportError:
    from io import StringIO as IO  # for legacy python

DISPLAY_LENGTH = 8


def records_by_auth(user: User):
    if user.is_staff:
        return Record.objects.all()
    else:
        return Record.objects.filter(pub_user=user)


def kols_by_auth(user: User):
    if user.groups.filter(name="KOL信息贡献者").exists():
        if user.is_staff:
            return Kol.objects.all().order_by("name")
        else:
            return Kol.objects.filter(pub_user=user)
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
            | Q(feedback__icontains=kw_list[0])  # 搜索主要反馈
        )
        for k in kw_list[1:]:
            search_condition.add(
                Q(kol__name__icontains=k)  # 搜索KOL姓名
                | Q(kol__hospital__name__icontains=k)  # 搜索供职医院名称
                | Q(purpose__icontains=k)  # 搜索拜访目标
                | Q(feedback__icontains=k),  # 搜索主要反馈
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
            attitude_1=int(request.POST.get("attitude_1")),
            attitude_2=int(request.POST.get("attitude_2")),
            attitude_3=int(request.POST.get("attitude_3")),
            attitude_4=int(request.POST.get("attitude_4")),
            attitude_5=int(request.POST.get("attitude_5")),
            feedback=request.POST.get("text_feedback"),
            pub_user=request.user,
        )
        obj.save()

        return redirect(reverse("kol:records"))
    else:
        kols = kols_by_auth(request.user)
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

        # # 准备治疗观念选项
        # attitudes = {}
        # for i in range(4):
        #     attitudes[Record._meta.get_field(f"attitude_{i}").verbose_name] = eval(
        #         f"ATTITUDE_{i}"
        #     )
        context = {
            "attitude_1_choices": Record.ATTITUDE_1_CHOICES,
            "attitude_2_choices": Record.ATTITUDE_2_CHOICES,
            "attitude_3_choices": Record.ATTITUDE_3_CHOICES,
            "attitude_4_choices": Record.ATTITUDE_4_CHOICES,
            "attitude_5_choices": Record.ATTITUDE_5_CHOICES,
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
        obj.attitude_1 = int(request.POST.get("attitude_1"))
        obj.attitude_2 = int(request.POST.get("attitude_2"))
        obj.attitude_3 = int(request.POST.get("attitude_3"))
        obj.attitude_4 = int(request.POST.get("attitude_4"))
        obj.attitude_5 = int(request.POST.get("attitude_5"))
        obj.feedback = request.POST.get("text_feedback")
        obj.upload_date = timezone.now()
        # obj.pub_user = request.user
        obj.save()

        # for file in request.FILES:
        #     obj_attachment = Attachment(record=obj, file=file)
        #     obj_attachment.save()

        return redirect(reverse("kol:records"))
    else:
        kols = kols_by_auth(request.user)
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
            "attitude_1_choices": Record.ATTITUDE_1_CHOICES,
            "attitude_2_choices": Record.ATTITUDE_2_CHOICES,
            "attitude_3_choices": Record.ATTITUDE_3_CHOICES,
            "attitude_4_choices": Record.ATTITUDE_4_CHOICES,
            "attitude_5_choices": Record.ATTITUDE_5_CHOICES,
            "record": Record.objects.get(pk=pk),
            # "attachments": Attachment.objects.filter(record=Record.objects.get(pk=pk)),
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


@login_required()
def export_record(request):
    records = records_by_auth(request.user)
    df = pd.DataFrame(
        list(
            records.values(
                "visit_date",
                "kol__name",
                "kol__hospital__xltid",
                "kol__hospital__province",
                "kol__hospital__city",
                "kol__hospital__decile",
                "kol__hospital__name",
                "kol__rating_infl",
                "kol__rating_prof",
                "kol__rating_fav",
                "kol__titles",
                "purpose",
                "attitude_1",
                "attitude_2",
                "attitude_3",
                "attitude_4",
                "attitude_5",
                "feedback",
                "upload_date",
                "pub_user__username",
            )
        )
    )
    df["upload_date"] = df["upload_date"].dt.tz_localize(
        None
    )  # Excel不支持带有时区的时间格式，导出会报错
    df.columns = [
        "拜访日期",
        "KOL姓名",
        "医院编码",
        "省份",
        "城市",
        "医院Decile",
        "医院名称",
        "影响力",
        "专业度",
        "支持度",
        "头衔&荣誉",
        "拜访目的",
        "观念_EPO浓度\n3_HIF-PHI在疗效保证前提下，刺激产生内源性EPO越接近生理浓度越好\n2_HIF-PHI在疗效保证前提下，EPO浓度无所谓\n1_HIF-PHI治疗，内源性EPO越高，疗效会越好\n0_本次拜访未涉及",
        "观念_升速稳定性\n3_Hb升速需适中，1-2g/dl最佳\n2_Hb升速慢点无所谓\n1_Hb需尽快达标，每月＞2g/dl危害不大\n0_本次拜访未涉及",
        "观念_PHD选择性\n3_选择性抑制PHD1及PHD3更高的HIF-PHI，更有利于HIF2α稳定，改善铁代谢更好\n2_不了解铁代谢与PHD不同亚型作用的相关性\n1_铁代谢与PHD不同亚型作用无相关性\n0_本次拜访未涉及",
        "观念_升速与血栓\n3_Hb升速波动过大会增加血栓事件风险\n2_不清楚Hb升速波动与血栓事件相关性\n1_Hb升速波动过大与血栓事件无相关性\n0_本次拜访未涉及",
        "观念_脱靶效应\n3_HIF-PHI对脂代谢的影响是“脱靶效应”的表现，HIF应更聚焦于红细胞生成\n2_不清楚HIF-PHI对脂代谢的改变对患者的远期影响\n1_HIF-PHI对脂代谢的影响是对患者的获益\n0_本次拜访未涉及",
        "主要反馈",
        "上传日期",
        "上传用户",
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
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    response["Content-Disposition"] = "attachment; filename=" + now + ".xlsx"
    return response


@login_required
def kols(request: request) -> HttpResponse:
    print(request.GET)
    param_dict = get_param(request.GET)

    kols = kols_by_auth(request.user)

    # 根据搜索筛选KOL
    kw = param_dict["kw"]
    if kw is not None:
        kw_list = kw.split(" ")

        search_condition = (
            Q(name__icontains=kw_list[0])  # 搜索KOL姓名
            | Q(hospital__name__icontains=kw_list[0])  # 搜索供职医院名称
            | Q(titles__icontains=kw_list[0])  # 搜索头衔和荣誉
        )
        for k in kw_list[1:]:
            search_condition.add(
                Q(name__icontains=k)  # 搜索KOL姓名
                | Q(hospital__name__icontains=k)  # 搜索供职医院名称
                | Q(titles__icontains=k),  # 搜索头衔和荣誉
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
            # dept=request.POST.get("dept"),
            rating_infl=int(request.POST.get("rating_infl")),
            rating_prof=int(request.POST.get("rating_prof")),
            rating_fav=int(request.POST.get("rating_fav")),
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
        # obj.dept = request.POST.get("dept")
        obj.rating_infl = int(request.POST.get("rating_infl"))
        obj.rating_prof = int(request.POST.get("rating_prof"))
        obj.rating_fav = int(request.POST.get("rating_fav"))
        obj.titles = request.POST.get("text_title")
        obj.upload_date = timezone.now()
        # obj.pub_user = request.user

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


@login_required()
def export_kol(request):
    kols = kols_by_auth(request.user)
    df = pd.DataFrame(
        list(
            kols.values(
                "name",
                "hospital__xltid",
                "hospital__province",
                "hospital__city",
                "hospital__decile",
                "hospital__name",
                "rating_infl",
                "rating_prof",
                "rating_fav",
                "titles",
                "upload_date",
                "pub_user__username",
            )
        )
    )
    df["upload_date"] = df["upload_date"].dt.tz_localize(
        None
    )  # Excel不支持带有时区的时间格式，导出会报错
    df.columns = [
        "KOL姓名",
        "医院编码",
        "省份",
        "城市",
        "医院Decile",
        "医院名称",
        "影响力",
        "专业度",
        "支持度",
        "头衔&荣誉",
        "上传日期",
        "上传用户",
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
    now = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    response["Content-Disposition"] = "attachment; filename=" + now + ".xlsx"
    return response


def bad_request(message):
    response = HttpResponse(
        json.dumps({"message": message}), content_type="application/json"
    )
    response.status_code = 400
    return response


def search_hps(request, kw):
    hospitals = Hospital.objects.filter(name__icontains=kw).order_by("-decile")[:10]
    try:
        results_list = []
        for hp in hospitals:
            option_dict = {
                "name": str(hp),
                "value": hp.pk,
            }
            results_list.append(option_dict)
        res = {
            "success": True,
            "results": results_list,
            "code": 200,
        }
    except Exception as e:
        res = {
            "success": False,
            "errMsg": e,
            "code": 0,
        }
    return HttpResponse(
        json.dumps(res, ensure_ascii=False),
        content_type="application/json charset=utf-8",
    )  # 返回结果必须是json格式

