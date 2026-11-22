from django.contrib import admin
from .models import Order, OperationAllocation


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ('order_no', 'style', 'buyer', 'order_qty', 'status', 'order_date')
    list_filter = ('status',)
    search_fields = ('order_no', 'style', 'buyer')


@admin.register(OperationAllocation)
class OperationAllocationAdmin(admin.ModelAdmin):
    list_display = (
        'date', 'team', 'operator', 'order',
        'operation', 'line_type', 'target_per_hour',
        'hours', 'planned_output'
    )
    list_filter = ('date', 'team', 'line_type')
    search_fields = ('operator__full_name', 'order__order_no')
    readonly_fields = ('planned_output',)
    date_hierarchy = 'date'