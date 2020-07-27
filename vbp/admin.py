from django.contrib import admin
from django import forms
from .models import *


# class VolumeForm(forms.ModelForm):
#     def __init__(self, *args, **kwargs):
#         super(VolumeForm, self).__init__(*args, **kwargs)
#         winner = Bid.objects.filter(record__tender_id=self.instance.tender_id)
#         w = self.fields['winner'].widget
#         choices = []
#         for choice in winner:
#             choices.append((choice.id, choice.__str__()))
#         w.choices = choices
#
#
#
# class VolumeAdmin(admin.ModelAdmin):
#     filter_horizontal = ('winner',)
#     form = VolumeForm


# admin.site.register(Volume, VolumeAdmin)
admin.site.register([Tender,
                     Company,
                     Bid,
                     Volume
                     ])