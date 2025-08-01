"""
URL patterns for delivery endpoints.
"""
from django.urls import path
from .views import (
    DeliveryRequestListView,
    DeliveryRequestDetailView,
    AssignedDeliveryRequestListView,
    customer_statistics_view,
    directions_view,
    sync_pending_view,
    sync_status_view,
    statistics_view,
    driver_statistics_view,
    get_available_partners,
    debug_list_all_requests,
)

urlpatterns = [
    # Delivery requests
    path('delivery-requests/', DeliveryRequestListView.as_view(), name='delivery-requests'),
    path('delivery-requests/<int:pk>/', DeliveryRequestDetailView.as_view(), name='delivery-request-detail'),
    path('delivery-requests/assigned/', AssignedDeliveryRequestListView.as_view(), name='assigned-delivery-requests'),
    
    # Partners
    path('partners/', get_available_partners, name='available-partners'),
    
    # Directions
    path('directions/', directions_view, name='directions'),
    
    # Sync
    path('sync/pending/', sync_pending_view, name='sync-pending'),
    path('sync/status/', sync_status_view, name='sync-status'),
    
    # Statistics
    path('statistics/', statistics_view, name='statistics'),
    path('statistics/driver/', driver_statistics_view, name='driver-statistics'),
     path('statistics/customer/', customer_statistics_view, name='customer-statistics'),
    # Debug
    path('debug/requests/', debug_list_all_requests, name='debug-requests'),
] 