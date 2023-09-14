from django.contrib import admin

from .models import *

# class AttachmentAdmin(admin.ModelAdmin):
#     pass

# class AttachmentsInline(admin.StackedInline):
#     model = Attachment
#     max_num = 10
#     extra = 0


class HospitalAdmin(admin.ModelAdmin):
    class Meta:
        model = Hospital

    search_fields = [
        "name",
        "xltid",
        "province",
        "city"
    ]


class KolAdmin(admin.ModelAdmin):
    class Meta:
        model = Kol

    search_fields = [
        "name",
        "hospital__xltid",
        "hospital__name",
    ]
    
class RecordAdmin(admin.ModelAdmin):
    class Meta:
        model = Record

    search_fields = [
        "kol__name",
        "kol__hospital__xltid",
        "kol__hospital__name",
        'user__username'
    ]

    # inlines = [
    #     AttachmentsInline,
    # ]

admin.site.register(Record, RecordAdmin)
admin.site.register(Kol, KolAdmin)
admin.site.register(Hospital, HospitalAdmin)


