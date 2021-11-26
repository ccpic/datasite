from django.contrib import admin
from .models import Announce


class AnnounceAdmin(admin.ModelAdmin):
    search_fields = ['title', 'source', 'url']
    
    
admin.site.register(Announce, AnnounceAdmin)
