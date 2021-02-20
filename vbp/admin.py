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

class TenderAdmin(admin.ModelAdmin):
    search_fields = ['vol', 'target']

class BidAdmin(admin.ModelAdmin):
    search_fields = ['tender__vol', 'tender__target', 'bidder__full_name']

class VolumeAdmin(admin.ModelAdmin):
    search_fields = ['tender__vol', 'tender__target']

admin.site.register(Tender, TenderAdmin)
admin.site.register(Bid, BidAdmin)
admin.site.register(Volume, VolumeAdmin)
admin.site.register([Company, Doc])