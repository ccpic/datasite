from django import template

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


@register.filter(name="objs_id_to_string")
def objs_id_to_string(objs):
    arr = []
    for obj in objs:
        arr.append(str(obj.pk))
    return "|".join(arr)


@register.filter(name="times")
def times(number):
    return range(number)


@register.simple_tag
def volume_win(bid, spec=None, region=None):
    try:
        volume = bid.std_volume_win(spec, region)
        if volume == 0:
            return ""
        else:
            return "{0:,.1f}".format(volume)
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
