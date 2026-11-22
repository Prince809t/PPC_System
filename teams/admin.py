
# Register your models here.
from django.contrib import admin
from .models import Team, Operator, Machine, Operation


@admin.register(Operation)
class OperationAdmin(admin.ModelAdmin):
    list_display = ('name', 'section', 'is_active')
    list_filter = ('section', 'is_active')
    search_fields = ('name',)


@admin.register(Machine)
class MachineAdmin(admin.ModelAdmin):
    list_display = ('machine_no', 'machine_type', 'is_active')
    list_filter = ('machine_type', 'is_active')
    search_fields = ('machine_no',)


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ('name', 'supervisor', 'shift_hours', 'effective_from', 'is_active')
    list_filter = ('is_active',)
    search_fields = ('name',)


@admin.register(Operator)
class OperatorAdmin(admin.ModelAdmin):
    list_display = (
        'full_name', 'employee_code', 'team',
        'operator_type', 'default_operation', 'default_machine',
        'target_per_hour', 'planned_per_day', 'is_active'
    )
    list_filter = ('team', 'operator_type', 'is_active')
    search_fields = ('full_name', 'employee_code')
    readonly_fields = ('planned_per_day',)