from django.contrib import admin
from .models import (
    FaultCode, InitialQualityReport, InitialQualityFault,
    FinalQualityReport, FinalQualityFault
)


@admin.register(FaultCode)
class FaultCodeAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('code', 'name')


class InitialQualityFaultInline(admin.TabularInline):
    model = InitialQualityFault
    extra = 1


@admin.register(InitialQualityReport)
class InitialQualityReportAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'order', 'team', 'qc_inspector',
        'total_qty_checked', 'total_qty_defective', 'defect_rate'
    )
    list_filter = ('date', 'team')
    search_fields = ('order__order_no',)
    date_hierarchy = 'date'
    inlines = [InitialQualityFaultInline]


class FinalQualityFaultInline(admin.TabularInline):
    model = FinalQualityFault
    extra = 1


@admin.register(FinalQualityReport)
class FinalQualityReportAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'order', 'team', 'qc_inspector',
        'qty_presented_at_final', 'qty_defective_at_final',
        'final_defect_rate', 'total_rework_hours'
    )
    list_filter = ('date', 'team')
    search_fields = ('order__order_no',)
    date_hierarchy = 'date'
    inlines = [FinalQualityFaultInline]