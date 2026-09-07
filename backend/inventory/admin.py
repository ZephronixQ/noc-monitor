from django.contrib import admin
from .models import Cluster, Switch, OltDevice, Incident


@admin.register(Cluster)
class ClusterAdmin(admin.ModelAdmin):
    list_display = ('name', 'switches_count', 'order')
    search_fields = ('name',)

    def switches_count(self, obj):
        return obj.switches.count()
    switches_count.short_description = "Кол-во коммутаторов"


@admin.register(Switch)
class SwitchAdmin(admin.ModelAdmin):
    list_display = ('ip', 'description', 'cluster', 'is_active')
    list_filter = ('cluster', 'is_active')
    search_fields = ('ip', 'description')
    list_editable = ('is_active',)


@admin.register(OltDevice)
class OltDeviceAdmin(admin.ModelAdmin):
    list_display = ('ip', 'model_type', 'port', 'is_active')
    list_filter = ('model_type', 'is_active')
    search_fields = ('ip',)
    list_editable = ('is_active',)


@admin.register(Incident)
class IncidentAdmin(admin.ModelAdmin):
    list_display = ('target_id', 'device_type', 'start_time_human', 'end_time_human', 'duration_str', 'is_active')
    list_filter = ('device_type', ('end_time', admin.EmptyFieldListFilter))
    search_fields = ('target_id',)
    readonly_fields = ('start_time', 'end_time', 'duration')

    def start_time_human(self, obj):
        from datetime import datetime
        return datetime.fromtimestamp(obj.start_time).strftime('%d.%m.%Y %H:%M:%S')
    start_time_human.short_description = "Начало"

    def end_time_human(self, obj):
        if not obj.end_time:
            return "🔴 Активна сейчас"
        from datetime import datetime
        return datetime.fromtimestamp(obj.end_time).strftime('%d.%m.%Y %H:%M:%S')
    end_time_human.short_description = "Конец"

    def duration_str(self, obj):
        m = obj.duration // 60
        h = m // 60
        return f"{h} ч {m % 60} мин" if h > 0 else f"{m} мин"
    duration_str.short_description = "Простой"