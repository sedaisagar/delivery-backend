"""
Serializers for delivery requests and related functionality.
"""
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import DeliveryRequest, Route, Statistics

User = get_user_model()


class PickupCoordinatesSerializer(serializers.Serializer):
    """
    Serializer for pickup coordinates.
    """
    latitude = serializers.FloatField(help_text="Pickup latitude")
    longitude = serializers.FloatField(help_text="Pickup longitude")


class DropoffCoordinatesSerializer(serializers.Serializer):
    """
    Serializer for dropoff coordinates.
    """
    latitude = serializers.FloatField(help_text="Dropoff latitude")
    longitude = serializers.FloatField(help_text="Dropoff longitude")


class CoordinatesSerializer(serializers.Serializer):
    """
    Serializer for coordinates structure.
    """
    pickup = PickupCoordinatesSerializer(help_text="Pickup coordinates")
    dropoff = DropoffCoordinatesSerializer(help_text="Dropoff coordinates")


class DeliveryRequestSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery requests.
    """
    coordinates = serializers.SerializerMethodField()
    customer_email = serializers.CharField(source='customer.email', read_only=True)
    driver_email = serializers.CharField(source='driver.email', read_only=True)
    driver_name = serializers.CharField(source='driver.first_name', read_only=True)
    assigned_by_email = serializers.CharField(source='assigned_by.email', read_only=True)
    
    class Meta:
        model = DeliveryRequest
        fields = [
            'id', 'pickup_address', 'dropoff_address', 'customer_name', 'customer_phone',
            'delivery_note', 'status', 'sync_status', 'pending_sync', 'coordinates', 
            'created_at', 'updated_at', 'synced_at', 'assigned_at',
            'customer_email', 'driver_email', 'assigned_by_email', 'driver_name'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'synced_at', 'assigned_at']
    
    def get_coordinates(self, obj):
        return obj.coordinates


class DeliveryRequestCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating delivery requests.
    """
    coordinates = CoordinatesSerializer(required=False)
    local_id = serializers.CharField(required=False, help_text='Local ID for offline sync')
    
    class Meta:
        model = DeliveryRequest
        fields = [
            'pickup_address', 'dropoff_address', 'customer_name', 'customer_phone',
            'delivery_note', 'coordinates', 'pending_sync', 'local_id'
        ]
    
    def create(self, validated_data):
        coordinates = validated_data.pop('coordinates', {})
        local_id = validated_data.pop('local_id', None)
        
        # Extract coordinates if provided
        if coordinates:
            pickup_coords = coordinates.get('pickup', {})
            dropoff_coords = coordinates.get('dropoff', {})
            
            validated_data['pickup_latitude'] = pickup_coords.get('latitude')
            validated_data['pickup_longitude'] = pickup_coords.get('longitude')
            validated_data['dropoff_latitude'] = dropoff_coords.get('latitude')
            validated_data['dropoff_longitude'] = dropoff_coords.get('longitude')
        
        # Set sync status based on pending_sync
        if validated_data.get('pending_sync', False):
            validated_data['sync_status'] = 'pending'
        
        return super().create(validated_data)
    
    def to_internal_value(self, data):
        """
        Override to handle coordinates properly for sync operations.
        """
        # Extract coordinates before validation
        coordinates = data.get('coordinates', {})
        
        # Convert coordinates to proper format if needed
        if coordinates and isinstance(coordinates, dict):
            # Ensure coordinates have proper structure
            if 'pickup' not in coordinates:
                coordinates['pickup'] = {}
            if 'dropoff' not in coordinates:
                coordinates['dropoff'] = {}
        
        return super().to_internal_value(data)


class DeliveryRequestUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating delivery requests.
    """
    driver = serializers.PrimaryKeyRelatedField(queryset=User.objects.filter(role='driver'), required=False, help_text='Driver ID to assign')
    
    class Meta:
        model = DeliveryRequest
        fields = ['status', 'driver']
    
    def update(self, instance:DeliveryRequest, validated_data):
        # Update status
        if 'status' in validated_data:
            instance.status = validated_data['status']
        
        # Update driver
        if 'driver' in validated_data:
            instance.driver = validated_data['driver']
            instance.status = 'assigned'
            instance.assigned_at = timezone.now()
        
        instance.save()
        return instance


class RouteSerializer(serializers.ModelSerializer):
    """
    Serializer for routes.
    """
    points = serializers.SerializerMethodField()
    
    class Meta:
        model = Route
        fields = ['distance', 'duration', 'polyline', 'mode', 'points']
    
    def get_points(self, obj):
        # This would typically decode the polyline to get points
        # For now, return a placeholder
        return []


class StatisticsSerializer(serializers.ModelSerializer):
    """
    Serializer for delivery statistics.
    """
    class Meta:
        model = Statistics
        fields = [
            'total_deliveries', 'completed_deliveries', 'pending_deliveries',
            'in_progress_deliveries', 'total_distance', 'total_earnings',
            'average_rating', 'on_time_delivery_rate'
        ]


class SyncRequestSerializer(serializers.Serializer):
    """
    Serializer for sync requests.
    """
    requests = DeliveryRequestCreateSerializer(many=True)


class SyncResponseSerializer(serializers.Serializer):
    """
    Serializer for sync responses.
    """
    synced = serializers.ListField()
    failed = serializers.ListField()
    conflicts = serializers.ListField()


class DirectionsRequestSerializer(serializers.Serializer):
    """
    Serializer for directions requests.
    """
    pickup_lat = serializers.FloatField()
    pickup_lng = serializers.FloatField()
    dropoff_lat = serializers.FloatField()
    dropoff_lng = serializers.FloatField()
    mode = serializers.ChoiceField(choices=['driving', 'walking', 'bicycling'], default='driving')


class DirectionsResponseSerializer(serializers.Serializer):
    """
    Serializer for directions responses.
    """
    route = serializers.DictField()


class PartnerSerializer(serializers.Serializer):
    """
    Serializer for delivery partners.
    """
    id = serializers.IntegerField()
    name = serializers.CharField()
    email = serializers.EmailField()
    phone = serializers.CharField()
    rating = serializers.FloatField()
    distance = serializers.CharField()
    available = serializers.BooleanField() 