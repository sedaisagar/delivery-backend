"""
Admin configuration for delivery app.
"""
from django.contrib import admin
from .models import DeliveryRequest, Route, SyncLog, Statistics


@admin.register(DeliveryRequest)
class DeliveryRequestAdmin(admin.ModelAdmin):
    """
    Admin for DeliveryRequest model.
    """
    list_display = ['id', 'customer_name', 'pickup_address', 'dropoff_address', 'status', 'driver', 'created_at']
    list_filter = ['status', 'sync_status', 'created_at', 'driver']
    search_fields = ['customer_name', 'pickup_address', 'dropoff_address', 'customer_phone']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('pickup_address', 'dropoff_address', 'customer_name', 'customer_phone', 'delivery_note')
        }),
        ('Status & Tracking', {
            'fields': ('status', 'sync_status', 'driver')
        }),
        ('Coordinates', {
            'fields': ('pickup_latitude', 'pickup_longitude', 'dropoff_latitude', 'dropoff_longitude'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    """
    Admin for Route model.
    """
    list_display = ['delivery_request', 'distance', 'duration', 'mode', 'created_at']
    list_filter = ['mode', 'created_at']
    search_fields = ['delivery_request__customer_name']
    ordering = ['-created_at']


@admin.register(SyncLog)
class SyncLogAdmin(admin.ModelAdmin):
    """
    Admin for SyncLog model.
    """
    list_display = ['delivery_request', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['delivery_request__customer_name', 'message']
    ordering = ['-created_at']
    readonly_fields = ['created_at']


@admin.register(Statistics)
class StatisticsAdmin(admin.ModelAdmin):
    """
    Admin for Statistics model.
    """
    list_display = ['user', 'date', 'total_deliveries', 'completed_deliveries', 'total_earnings']
    list_filter = ['date', 'user']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    ordering = ['-date']
    readonly_fields = ['date'] 