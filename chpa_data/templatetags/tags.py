from django import template
register = template.Library()
from vbp.models import *

@register.filter(name='fix_decimal')
def fix_decimal(value, decimal=0):
    try:
        format_str = '{0:,.'+ str(decimal) + 'f}'
        return format_str.format(value)
    except:
        return value


@register.filter(name='percentage')
def percentage(value, decimal=0):
    try:
        format_str = '{0:.'+ str(decimal) + '%}'
        return format_str.format(value)
    except:
        return value


@register.simple_tag
def volume_win(bid, spec=None, region=None):
    try:
        volume = bid.std_volume_win(spec, region)
        return '{0:,.0f}'.format(volume)
    except:
        return None

@register.simple_tag
def volume_win_percentage(bid, region):
    volume_win = bid.std_volume_win(region=region)
    volume_total = bid.record.tender.total_std_volume_contract
    percentage = volume_win/volume_total
    return '{0:.1%}'.format(percentage)
