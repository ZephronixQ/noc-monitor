from django.contrib import admin
from django.urls import path

admin.site.site_header = "NOC MONITOR ENTERPRISE"
admin.site.site_title = "Панель управления инвентарем"
admin.site.index_title = "Управление сетевой инфраструктурой"

urlpatterns = [
    path("", admin.site.urls),
    path("admin/", admin.site.urls),
]