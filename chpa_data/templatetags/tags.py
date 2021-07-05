from medical_info.models import Program
from chpa_data.models import Record
from django import template
from re import IGNORECASE, compile, escape as rescape
from django.utils.safestring import mark_safe

register = template.Library()
from vbp.models import *


@register.filter(name="fix_decimal")
def fix_decimal(value, decimal=0):
    try:
        format_str = "{0:,." + str(decimal) + "f}"
        return format_str.format(value)
    except:
        return value


@register.filter(name="percentage")
def percentage(value, decimal=0):
    try:
        format_str = "{0:." + str(decimal) + "%}"
        return format_str.format(value)
    except:
        return value


@register.filter(name="zero_to_empty")
def zero_to_empty(value):
    try:
        if value == 0:
            return ""
    except:
        return value


@register.filter(name="order_by_std_price")
def order_by_std_price(qs, reverse=True):

    return sorted(qs, key=lambda a: a.std_price, reverse=reverse)


@register.filter(name="objs_id_to_string")
def objs_id_to_string(objs):
    arr = []
    for obj in objs:
        arr.append(str(obj.pk))
    return "|".join(arr)


@register.filter(name="times")
def times(number):
    try:
        return range(1, number + 1)
    except:
        return []


@register.simple_tag
def volume_win(bid, spec=None, region=None):
    try:
        volume = bid.std_volume_win(spec, region)
        if volume == 0:
            return ""
        else:
            return "{0:.1f}".format(volume)
    except:
        return None


@register.simple_tag
def volume_win_percentage(bid, region=None):
    if region is None:
        volume_win = bid.std_volume_win()
    else:
        volume_win = bid.std_volume_win(region=region)
    volume_total = bid.tender.total_std_volume_contract()
    percentage = volume_win / volume_total
    return "{0:.1%}".format(percentage)


@register.simple_tag
def winner(tender, region):
    qs = Volume.objects.filter(tender=tender, region=region)
    if qs.exists():
        return qs.first().winner
    else:
        return None


@register.simple_tag
def region_std_volume(tender, region):
    qs = Volume.objects.filter(tender=tender, region=region)
    if qs.exists():
        winner = qs.first().winner
        volume = winner.std_volume_win(region=region)
        return "{0:,.1f}".format(volume)
    else:
        return None


@register.simple_tag
def qs_by_competition(tenders, bidder_num, winner_num):
    tender_ids = [tender.id for tender in tenders if tender.bids.count() == bidder_num]
    qs = tenders.filter(id__in=tender_ids)
    tender_ids = [tender.id for tender in qs if tender.winners().count() == winner_num]
    qs = tenders.filter(id__in=tender_ids)
    return qs


@register.filter(name="change_unit")
def change_unit(value):
    try:
        value = value / 1000000
        if value == 0:
            format_str = ""
        elif value < 1:
            format_str = "{0:,.2f}"
        else:
            format_str = "{0:,.0f}"
        return format_str.format(value)
    except:
        return ""


@register.filter(name="filter_fields")  # 从表单字典中提取数据筛选字段
def filter_fields(dict):
    new_dict = {}

    if dict["customized_sql"] != "":
        new_dict["customized_sql"] = [dict["customized_sql"]]
    else:
        for k, v in dict.items():
            if k[-2:] == "[]":
                if isinstance(v, list):
                    new_dict[k[:-9]] = v
                else:
                    new_dict[k[:-9]] = [v]
    return new_dict


@register.filter(name="get_record")
def get_record(pk):
    obj = Record.objects.get(id=pk)
    return obj.args


@register.filter(name="highlight")
def highlight(text, search):
    try:
        rgx = compile(rescape(search), IGNORECASE)
        return mark_safe(
            rgx.sub(lambda m: '<b class="highlight">{}</b>'.format(m.group()), text)
        )
    except:
        return text
    
    
@register.inclusion_tag('medical_info/programs.html')
def show_programs():
    programs = Program.objects.all()
    return {'programs': programs}