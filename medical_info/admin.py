from django.contrib import admin
from taggit.forms import TagField
from taggit_labels.widgets import LabelWidget
from .models import *
from django import forms


class ImagesAdmin(admin.ModelAdmin):
    pass


class ImagesInline(admin.StackedInline):
    model = Images
    max_num = 10
    extra = 0


class FilesAdmin(admin.ModelAdmin):
    pass


class FilesInline(admin.StackedInline):
    model = Files
    max_num = 10
    extra = 0


class ContentForm(forms.ModelForm):
    tags = TagField(required=False, widget=LabelWidget)


class PostAdmin(admin.ModelAdmin):
    search_fields = [
        "title_cn",
        "title_en",
        "program__name",
        "program__vol",
        "pub_agent__full_name",
        "pub_agent__abbr_name",
    ]
    # form = ContentForm
    inlines = [
        ImagesInline,
        FilesInline,
    ]


admin.site.register(Images, ImagesAdmin)
admin.site.register(Files, FilesAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register([PubAgent, Program])

