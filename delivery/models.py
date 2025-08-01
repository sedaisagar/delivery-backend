"""
Models for delivery requests and related functionality.
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class DeliveryRequest(models.Model):
    """
    Model for delivery requests.
    """
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('assigned', 'Assigned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]
    
    SYNC_STATUS_CHOICES = [
        ('synced', 'Synced'),
        ('pending', 'Pending'),
        ('failed', 'Failed'),
    ]
    
    # Basic information
    pickup_address = models.CharField(max_length=500)
    dropoff_address = models.CharField(max_length=500)
    customer_name = models.CharField(max_length=100)
    customer_phone = models.CharField(max_length=20)
    delivery_note = models.TextField(blank=True)
    
    # Status and tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sync_status = models.CharField(max_length=20, choices=SYNC_STATUS_CHOICES, default='synced')
    pending_sync = models.BooleanField(default=False, help_text='Indicates if this request was created offline')
    
    # Coordinates
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dropoff_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    dropoff_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    
    # Relationships
    customer = models.ForeignKey(User, on_delete=models.CASCADE, related_name='customer_deliveries', help_text='Customer who created this request')
    driver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='driver_deliveries', help_text='Driver assigned to this request')
    assigned_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='assigned_deliveries', help_text='Admin who assigned the driver')
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    synced_at = models.DateTimeField(null=True, blank=True)
    assigned_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Delivery {self.id} - {self.customer_name}"
    
    @property
    def coordinates(self):
        """Return coordinates in the format expected by the API."""
        return {
            'pickup': {
                'latitude': float(self.pickup_latitude) if self.pickup_latitude else None,
                'longitude': float(self.pickup_longitude) if self.pickup_longitude else None,
            },
            'dropoff': {
                'latitude': float(self.dropoff_latitude) if self.dropoff_latitude else None,
                'longitude': float(self.dropoff_longitude) if self.dropoff_longitude else None,
            }
        }
    
    def mark_as_synced(self):
        """Mark the request as synced with the server."""
        self.sync_status = 'synced'
        self.pending_sync = False
        self.synced_at = timezone.now()
        self.save()
    
    def assign_driver(self, driver, assigned_by=None):
        """Assign a driver to this delivery request."""
        self.driver = driver
        self.status = 'assigned'
        self.assigned_by = assigned_by
        self.assigned_at = timezone.now()
        self.save()


class Route(models.Model):
    """
    Model for storing route information.
    """
    delivery_request = models.OneToOneField(DeliveryRequest, on_delete=models.CASCADE, related_name='route')
    distance = models.CharField(max_length=50)  # e.g., "2.5 km"
    duration = models.CharField(max_length=50)  # e.g., "8 mins"
    polyline = models.TextField()  # Encoded polyline string
    mode = models.CharField(max_length=20, default='driving')  # driving, walking, bicycling
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Route for Delivery {self.delivery_request.id}"


class SyncLog(models.Model):
    """
    Model for tracking sync operations.
    """
    delivery_request = models.ForeignKey(DeliveryRequest, on_delete=models.CASCADE, related_name='sync_logs')
    status = models.CharField(max_length=20)  # success, failed
    message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Sync log for Delivery {self.delivery_request.id} - {self.status}"


class Statistics(models.Model):
    """
    Model for storing delivery statistics.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='statistics')
    date = models.DateField()
    total_deliveries = models.IntegerField(default=0)
    completed_deliveries = models.IntegerField(default=0)
    pending_deliveries = models.IntegerField(default=0)
    in_progress_deliveries = models.IntegerField(default=0)
    total_distance = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total_earnings = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    on_time_delivery_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    class Meta:
        unique_together = ['user', 'date']
        ordering = ['-date']
    
    def __str__(self):
        return f"Statistics for {self.user.email} on {self.date}" 