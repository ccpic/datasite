from django.contrib import admin
from .models import *

admin.site.register([Company, Drug, Sales])

