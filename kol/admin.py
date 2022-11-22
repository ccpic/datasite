from django.contrib import admin
from .models import *


class AttachmentAdmin(admin.ModelAdmin):
    pass

class AttachmentsInline(admin.StackedInline):
    model = Attachment
    max_num = 10
    extra = 0


class RecordAdmin(admin.ModelAdmin):
    class Meta:
        model = Record

    search_fields = [
        "kol__name",
        "kol__hospital__xltid",
        "kol__hospital__name",
    ]

    inlines = [
        AttachmentsInline,
    ]

admin.site.register(Record, RecordAdmin)
admin.site.register([Hospital, Kol])

