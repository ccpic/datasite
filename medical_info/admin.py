from django.contrib import admin
from django.forms import fields, widgets
from taggit.forms import TagField
from taggit.models import Tag
from django.forms import Textarea

from taggit_labels.widgets import LabelWidget
from .models import *
from django import forms
from django.contrib.admin.widgets import FilteredSelectMultiple
from django.contrib.admin.widgets import AdminTextareaWidget
import six
from taggit.utils import edit_string_for_tags


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


# class TagForm(forms.ModelForm):
#     tags = TagField(required=False, widget=LabelWidget)


# class TagMultipleChoiceField(forms.ModelMultipleChoiceField):
#     def prepare_value(self, value):
#         if hasattr(value, "tag_id"):
#             return value.tag_id
#         elif (
#             hasattr(value, "__iter__")
#             and not isinstance(value, six.text_type)
#             and not hasattr(value, "_meta")
#         ):
#             return [self.prepare_value(v) for v in value]
#         else:
#             return super(TagMultipleChoiceField, self).prepare_value(value)


class TaggitAdminTextareaWidget(AdminTextareaWidget):
    # taken from taggit.forms.TagWidget
    def render(self, name, value, attrs=None, renderer=None):
        attrs={'rows': 2}
        if value is not None and not isinstance(value, six.string_types):
            value = edit_string_for_tags([o for o in value])
        return super(TaggitAdminTextareaWidget, self).render(name, value, attrs)


class TagForm(forms.ModelForm):
    class Meta:
        model = Post
        exclude = ()
        widgets = {"tags": TaggitAdminTextareaWidget}


class PostAdmin(admin.ModelAdmin):
    class Meta:
        model = Post

    search_fields = [
        "title_cn",
        "title_en",
        "program__name",
        "program__vol",
        "pub_agent__full_name",
        "pub_agent__abbr_name",
    ]

    inlines = [
        ImagesInline,
        FilesInline,
    ]
    form = TagForm
    filter_horizontal = ("nation",)


# admin.site.register(Images, ImagesAdmin)
# admin.site.register(Files, FilesAdmin)
admin.site.register(Post, PostAdmin)
admin.site.register([PubAgent, Program, Nation])

