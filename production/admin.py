from django.contrib import admin
from .models import OutputLog, DowntimeLog


@admin.register(OutputLog)
class OutputLogAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'operator', 'team', 'order', 'operation',
        'start_time', 'end_time', 'pieces_completed', 'qc_checked'
    )
    list_filter = ('date', 'team', 'qc_checked')
    search_fields = ('operator__full_name', 'order__order_no')
    date_hierarchy = 'date'


@admin.register(DowntimeLog)
class DowntimeLogAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'operator', 'team', 'reason',
        'start_time', 'end_time'
    )
    list_filter = ('date', 'team', 'reason')
    search_fields = ('operator__full_name',)
    date_hierarchy = 'date'