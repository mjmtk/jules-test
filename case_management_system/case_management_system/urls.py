# case_management_system/urls.py
from django.contrib import admin
from django.urls import path
from core.api import api as core_api

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/v1/', core_api.urls), # Include core api under /api/v1/
]
