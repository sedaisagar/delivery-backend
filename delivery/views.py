"""
Views for delivery requests and related functionality.
"""
from rest_framework import status, generics, filters
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.db import models
from django.utils import timezone
from datetime import datetime, timedelta
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import DeliveryRequest, Route, Statistics, SyncLog
from .serializers import (
    DeliveryRequestSerializer,
    DeliveryRequestCreateSerializer,
    DeliveryRequestUpdateSerializer,
    RouteSerializer,
    StatisticsSerializer,
    SyncRequestSerializer,
    SyncResponseSerializer,
    DirectionsRequestSerializer,
    DirectionsResponseSerializer,
)
from .permissions import (
    IsCustomer, IsDriver, IsAdmin, IsCustomerOrAdmin, 
    IsDriverOrAdmin, IsOwnerOrAdmin, MobileAppPermission
)
from django.contrib.auth import get_user_model
User = get_user_model()


class DeliveryRequestListView(generics.ListCreateAPIView):
    """
    View for listing and creating delivery requests.
    """
    serializer_class = DeliveryRequestSerializer
    permission_classes = [IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'sync_status', 'pending_sync']
    search_fields = ['customer_name', 'pickup_address', 'dropoff_address']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all requests
        if user.role == 'admin':
            return DeliveryRequest.objects.all()
        
        # Customer sees only their own requests
        elif user.role == 'customer':
            return DeliveryRequest.objects.filter(customer=user)
        
        # Driver sees only their assigned requests
        elif user.role == 'driver':
            return DeliveryRequest.objects.filter(driver=user)
        
        return DeliveryRequest.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'POST':
            return DeliveryRequestCreateSerializer
        return DeliveryRequestSerializer
    
    def get_permissions(self):
        """
        Only customers can create requests, admins can view all.
        """
        if self.request.method == 'POST':
            return [IsCustomer()]
        return [IsAuthenticated()]
    
    @extend_schema(
        tags=['delivery-requests'],
        summary='List Delivery Requests',
        description='Retrieve a paginated list of delivery requests with filtering and search capabilities.',
        parameters=[
            OpenApiParameter(name='status', description='Filter by delivery status', required=False, type=str),
            OpenApiParameter(name='sync_status', description='Filter by sync status', required=False, type=str),
            OpenApiParameter(name='pending_sync', description='Filter by pending sync status', required=False, type=bool),
            OpenApiParameter(name='search', description='Search in customer name and addresses', required=False, type=str),
            OpenApiParameter(name='ordering', description='Order by field (e.g., created_at, -updated_at)', required=False, type=str),
            OpenApiParameter(name='page', description='Page number', required=False, type=int),
        ],
        responses={200: DeliveryRequestSerializer}
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'success': True,
                'data': {
                    'requests': serializer.data,
                    'pagination': {
                        'page': self.paginator.page.number,
                        'limit': self.paginator.page_size,
                        'total': self.paginator.page.paginator.count,
                        'totalPages': self.paginator.page.paginator.num_pages,
                    }
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': {
                'requests': serializer.data,
                'pagination': {
                    'page': 1,
                    'limit': len(serializer.data),
                    'total': len(serializer.data),
                    'totalPages': 1,
                }
            }
        })
    
    @extend_schema(
        tags=['delivery-requests'],
        summary='Create Delivery Request',
        description='Create a new delivery request. Only customers can create requests.',
        examples=[
            OpenApiExample(
                'Online Delivery Request',
                value={
                    'pickup_address': '123 Main St, City',
                    'dropoff_address': '456 Oak Ave, Town',
                    'customer_name': 'John Doe',
                    'customer_phone': '+1234567890',
                    'delivery_note': 'Please ring doorbell',
                    'coordinates': {
                        'pickup': {
                            'latitude': 37.78825,
                            'longitude': -122.4324
                        },
                        'dropoff': {
                            'latitude': 37.78925,
                            'longitude': -122.4344
                        }
                    },
                    'pending_sync': False
                }
            ),
            OpenApiExample(
                'Offline Delivery Request',
                value={
                    'pickup_address': '123 Main St, City',
                    'dropoff_address': '456 Oak Ave, Town',
                    'customer_name': 'John Doe',
                    'customer_phone': '+1234567890',
                    'delivery_note': 'Please ring doorbell',
                    'coordinates': {
                        'pickup': {
                            'latitude': 37.78825,
                            'longitude': -122.4324
                        },
                        'dropoff': {
                            'latitude': 37.78925,
                            'longitude': -122.4344
                        }
                    },
                    'pending_sync': True
                }
            )
        ],
        responses={201: DeliveryRequestSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Set customer and sync status
        data = serializer.validated_data
        data['customer'] = request.user
        
        if data.get('pending_sync', False):
            data['sync_status'] = 'pending'
        
        delivery_request = serializer.save()
        
        response_serializer = DeliveryRequestSerializer(delivery_request)
        return Response({
            'success': True,
            'data': response_serializer.data
        }, status=status.HTTP_201_CREATED)


class DeliveryRequestDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    View for retrieving, updating, and deleting delivery requests.
    """
    serializer_class = DeliveryRequestSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        
        # Admin sees all requests
        if user.role == 'admin':
            return DeliveryRequest.objects.all()
        
        # Customer sees only their own requests
        elif user.role == 'customer':
            return DeliveryRequest.objects.filter(customer=user)
        
        # Driver sees only their assigned requests
        elif user.role == 'driver':
            return DeliveryRequest.objects.filter(driver=user)
        
        return DeliveryRequest.objects.none()
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return DeliveryRequestUpdateSerializer
        return DeliveryRequestSerializer
    
    @extend_schema(
        tags=['delivery-requests'],
        summary='Get Delivery Request',
        description='Retrieve detailed information about a specific delivery request.',
        responses={200: DeliveryRequestSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @extend_schema(
        tags=['delivery-requests'],
        summary='Update Delivery Request',
        description='Update the status of a delivery request. Admins can assign drivers.',
        examples=[
            OpenApiExample(
                'Update Status',
                value={
                    'status': 'in_progress'
                }
            ),
            OpenApiExample(
                'Assign Driver',
                value={
                    'driver': 1,
                    'status': 'assigned'
                }
            )
        ],
        responses={200: DeliveryRequestUpdateSerializer}
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        
        # Handle driver assignment
        if 'driver' in serializer.validated_data and request.user.role == 'admin':
            driver_id = serializer.validated_data.pop('driver')
            try:
                driver = User.objects.get(id=driver_id, role='driver')
                instance.assign_driver(driver, assigned_by=request.user)
            except User.DoesNotExist:
                return Response({
                    'success': False,
                    'error': 'Driver not found'
                }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer.save()
        
        return Response({
            'success': True,
            'data': {
                'id': instance.id,
                'status': instance.status,
                'driver': instance.driver.id if instance.driver else None,
                'updatedAt': instance.updated_at,
            }
        })
    
    @extend_schema(
        tags=['delivery-requests'],
        summary='Delete Delivery Request',
        description='Permanently delete a delivery request.',
        responses={200: {'type': 'object', 'properties': {'success': {'type': 'boolean'}, 'message': {'type': 'string'}}}}
    )
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response({
            'success': True,
            'message': 'Delivery request deleted successfully'
        })


class AssignedDeliveryRequestListView(generics.ListAPIView):
    """
    View for drivers to see their assigned delivery requests.
    """
    serializer_class = DeliveryRequestSerializer
    permission_classes = [IsDriver]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['customer_name', 'pickup_address', 'dropoff_address']
    ordering_fields = ['created_at', 'updated_at', 'status']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return DeliveryRequest.objects.filter(
            driver=self.request.user,
            status__in=['assigned', 'in_progress']
        )
    
    @extend_schema(
        tags=['delivery-requests'],
        summary='Get Assigned Delivery Requests',
        description='Retrieve delivery requests assigned to the current driver.',
        responses={200: DeliveryRequestSerializer}
    )
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return Response({
                'success': True,
                'data': {
                    'requests': serializer.data,
                    'pagination': {
                        'page': self.paginator.page.number,
                        'limit': self.paginator.page_size,
                        'total': self.paginator.page.paginator.count,
                        'totalPages': self.paginator.page.paginator.num_pages,
                    }
                }
            })
        
        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': {
                'requests': serializer.data,
                'pagination': {
                    'page': 1,
                    'limit': len(serializer.data),
                    'total': len(serializer.data),
                    'totalPages': 1,
                }
            }
        })


@extend_schema(
    tags=['partners'],
    summary='Get Available Partners',
    description='Retrieve a list of available delivery partners (drivers) for assignment.',
    parameters=[
        OpenApiParameter(name='location', description='Location to find nearby partners', required=False, type=str),
        OpenApiParameter(name='radius', description='Search radius in kilometers', required=False, type=float),
        OpenApiParameter(name='available_only', description='Show only available drivers', required=False, type=bool),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'data': {
                    'type': 'array',
                    'items': {
                        'type': 'object',
                        'properties': {
                            'id': {'type': 'integer'},
                            'name': {'type': 'string'},
                            'email': {'type': 'string'},
                            'phone': {'type': 'string'},
                            'rating': {'type': 'number'},
                            'distance': {'type': 'string'},
                            'available': {'type': 'boolean'},
                            'total_deliveries': {'type': 'integer'},
                            'completed_deliveries': {'type': 'integer'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_available_partners(request):
    """
    Get available delivery partners (drivers) for assignment.
    """
    # Get all users who are drivers
    drivers = User.objects.filter(role='driver')
    
    # Filter by availability if requested
    available_only = request.query_params.get('available_only', 'false').lower() == 'true'
    if available_only:
        # Get drivers who have less than 5 active deliveries
        drivers = drivers.annotate(
            active_deliveries=models.Count(
                'driver_deliveries',
                filter=models.Q(driver_deliveries__status__in=['assigned', 'in_progress'])
            )
        ).filter(active_deliveries__lt=5)
    
    partners = []
    for driver in drivers:
        # Calculate driver statistics
        total_deliveries = DeliveryRequest.objects.filter(driver=driver).count()
        completed_deliveries = DeliveryRequest.objects.filter(
            driver=driver, 
            status='completed'
        ).count()
        
        # Calculate active deliveries
        active_deliveries = DeliveryRequest.objects.filter(
            driver=driver,
            status__in=['assigned', 'in_progress']
        ).count()
        
        # Determine availability (available if less than 3 active deliveries)
        available = active_deliveries < 3
        
        # Mock rating and distance (in real implementation, these would be calculated)
        rating = 4.5 + (completed_deliveries * 0.01)  # Simple rating calculation
        distance = f"{2 + (driver.id % 5)}.{(driver.id % 10)} km"  # Mock distance
        
        partners.append({
            'id': driver.id,
            'name': f"{driver.first_name} {driver.last_name}".strip() or driver.username,
            'email': driver.email,
            'phone': driver.phone or 'N/A',
            'rating': round(rating, 1),
            'distance': distance,
            'available': available,
            'total_deliveries': total_deliveries,
            'completed_deliveries': completed_deliveries,
            'active_deliveries': active_deliveries
        })
    
    # Sort by availability and rating
    partners.sort(key=lambda x: (not x['available'], -x['rating']))
    
    return Response({
        'success': True,
        'data': partners
    })


@extend_schema(
    tags=['directions'],
    summary='Get Directions',
    description='Calculate route directions between pickup and dropoff locations.',
    parameters=[
        OpenApiParameter(name='pickup_lat', description='Pickup latitude', required=True, type=float),
        OpenApiParameter(name='pickup_lng', description='Pickup longitude', required=True, type=float),
        OpenApiParameter(name='dropoff_lat', description='Dropoff latitude', required=True, type=float),
        OpenApiParameter(name='dropoff_lng', description='Dropoff longitude', required=True, type=float),
        OpenApiParameter(name='mode', description='Travel mode (driving, walking, bicycling)', required=False, type=str),
    ],
    responses={200: DirectionsResponseSerializer}
)
@api_view(['GET'])
@permission_classes([MobileAppPermission])
def directions_view(request):
    """
    View for getting directions between two points.
    """
    serializer = DirectionsRequestSerializer(data=request.query_params)
    serializer.is_valid(raise_exception=True)
    
    # Extract parameters
    pickup_lat = serializer.validated_data['pickup_lat']
    pickup_lng = serializer.validated_data['pickup_lng']
    dropoff_lat = serializer.validated_data['dropoff_lat']
    dropoff_lng = serializer.validated_data['dropoff_lng']
    mode = serializer.validated_data['mode']
    
    # Mock route data (in real implementation, this would call a mapping service)
    route_data = {
        'points': [
            {'latitude': pickup_lat, 'longitude': pickup_lng},
            {'latitude': (pickup_lat + dropoff_lat) / 2, 'longitude': (pickup_lng + dropoff_lng) / 2},
            {'latitude': dropoff_lat, 'longitude': dropoff_lng}
        ],
        'distance': '2.5 km',
        'duration': '8 mins',
        'polyline': 'mock_polyline_string'
    }
    
    return Response({
        'success': True,
        'data': {
            'route': route_data
        }
    })


@extend_schema(
    tags=['sync'],
    summary='Sync Pending Requests',
    description='Synchronize pending delivery requests from offline storage.',
    request=SyncRequestSerializer,
    examples=[
        OpenApiExample(
            'Sync Offline Requests',
            value={
                'requests': [
                    {
                        'local_id': 'local_123',
                        'pickup_address': '123 Main St, City',
                        'dropoff_address': '456 Oak Ave, Town',
                        'customer_name': 'John Doe',
                        'customer_phone': '+1234567890',
                        'delivery_note': 'Please ring doorbell',
                        'pending_sync': True,
                        'coordinates': {
                            'pickup': {
                                'latitude': 37.78825,
                                'longitude': -122.4324
                            },
                            'dropoff': {
                                'latitude': 37.78925,
                                'longitude': -122.4344
                            }
                        }
                    }
                ]
            }
        )
    ],
    responses={200: SyncResponseSerializer}
)
@api_view(['POST'])
@permission_classes([MobileAppPermission])
def sync_pending_view(request):
    """
    View for syncing pending delivery requests.
    """
    serializer = SyncRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    
    requests_data = serializer.validated_data['requests']
    synced = []
    failed = []
    conflicts = []
    
    for request_data in requests_data:
        try:
            # Extract coordinates and local_id before creating/updating
            coordinates = request_data.pop('coordinates', {})
            local_id = request_data.pop('local_id', None)
            
            # Extract coordinate values
            pickup_coords = coordinates.get('pickup', {})
            dropoff_coords = coordinates.get('dropoff', {})
            
            # Add coordinate fields to request_data
            if pickup_coords:
                request_data['pickup_latitude'] = pickup_coords.get('latitude')
                request_data['pickup_longitude'] = pickup_coords.get('longitude')
            
            if dropoff_coords:
                request_data['dropoff_latitude'] = dropoff_coords.get('latitude')
                request_data['dropoff_longitude'] = dropoff_coords.get('longitude')
            
            # Set customer for new requests
            if request.user.role == 'customer':
                request_data['customer'] = request.user
            
            # Check if request already exists
            existing_request = None
            if local_id:
                # Try to find existing request by local ID or other unique identifier
                existing_request = DeliveryRequest.objects.filter(
                    customer=request.user,
                    customer_name=request_data.get('customer_name'),
                    customer_phone=request_data.get('customer_phone'),
                    pickup_address=request_data.get('pickup_address'),
                    created_at__date=timezone.now().date()
                ).first()
            
            if existing_request:
                # Update existing request - only update fields that can be set
                updateable_fields = [
                    'dropoff_address', 'customer_name', 'customer_phone', 
                    'delivery_note', 'pickup_latitude', 'pickup_longitude',
                    'dropoff_latitude', 'dropoff_longitude', 'status'
                ]
                
                for field in updateable_fields:
                    if field in request_data and hasattr(existing_request, field):
                        setattr(existing_request, field, request_data[field])
                
                existing_request.mark_as_synced()
                delivery_request = existing_request
                print(f"Updated existing request ID: {delivery_request.id}")
            else:
                # Create new request
                delivery_request = DeliveryRequest.objects.create(**request_data)
                delivery_request.mark_as_synced()
                print(f"Created new request ID: {delivery_request.id}")
            
            # Log sync
            SyncLog.objects.create(
                delivery_request=delivery_request,
                status='success',
                message=f'Successfully synced request ID: {delivery_request.id}'
            )
            
            synced.append({
                'localId': local_id or f'local_{delivery_request.id}',
                'serverId': delivery_request.id,
                'status': 'synced'
            })
            
            print(f"Synced - Local ID: {local_id}, Server ID: {delivery_request.id}")
            
        except Exception as e:
            failed.append({
                'localId': local_id or f'local_{len(failed) + 1}',
                'error': str(e)
            })
            print(f"Failed to sync - Local ID: {local_id}, Error: {str(e)}")
    
    return Response({
        'success': True,
        'data': {
            'synced': synced,
            'failed': failed,
            'conflicts': conflicts
        }
    })


@extend_schema(
    tags=['sync'],
    summary='Get Sync Status',
    description='Retrieve the current sync status and statistics.',
    responses={
        200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'lastSync': {'type': 'string', 'format': 'date-time'},
                        'pendingCount': {'type': 'integer'},
                        'failedCount': {'type': 'integer'},
                        'syncedCount': {'type': 'integer'},
                        'pendingRequests': {
                            'type': 'array',
                            'items': {'type': 'object'}
                        }
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([MobileAppPermission])
def sync_status_view(request):
    """
    View for getting sync status.
    """
    user = request.user
    
    # Get sync statistics based on user role
    if user.role == 'customer':
        # Customers see their own requests
        last_sync = SyncLog.objects.filter(
            delivery_request__customer=user
        ).order_by('-created_at').first()
        
        pending_requests = DeliveryRequest.objects.filter(
            customer=user, sync_status='pending'
        )
        
        failed_requests = DeliveryRequest.objects.filter(
            customer=user, sync_status='failed'
        )
        
        synced_requests = DeliveryRequest.objects.filter(
            customer=user, sync_status='synced'
        )
    else:  # driver
        # Drivers see their assigned requests
        last_sync = SyncLog.objects.filter(
            delivery_request__driver=user
        ).order_by('-created_at').first()
        
        pending_requests = DeliveryRequest.objects.filter(
            driver=user, sync_status='pending'
        )
        
        failed_requests = DeliveryRequest.objects.filter(
            driver=user, sync_status='failed'
        )
        
        synced_requests = DeliveryRequest.objects.filter(
            driver=user, sync_status='synced'
        )
    
    return Response({
        'success': True,
        'data': {
            'lastSync': last_sync.created_at.isoformat() if last_sync else None,
            'pendingCount': pending_requests.count(),
            'failedCount': failed_requests.count(),
            'syncedCount': synced_requests.count(),
            'pendingRequests': DeliveryRequestSerializer(pending_requests, many=True).data
        }
    })


@extend_schema(
    tags=['statistics'],
    summary='Get Delivery Statistics',
    description='Retrieve delivery statistics for the current user.',
    parameters=[
        OpenApiParameter(name='period', description='Time period (today, week, month, year)', required=False, type=str),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'totalDeliveries': {'type': 'integer'},
                        'completedDeliveries': {'type': 'integer'},
                        'pendingDeliveries': {'type': 'integer'},
                        'inProgressDeliveries': {'type': 'integer'},
                        'totalDistance': {'type': 'string'},
                        'totalEarnings': {'type': 'number'},
                        'averageRating': {'type': 'number'},
                        'onTimeDeliveryRate': {'type': 'number'}
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([MobileAppPermission])
def statistics_view(request):
    """
    View for getting delivery statistics.
    """
    user = request.user
    period = request.query_params.get('period', 'today')
    
    # Calculate date range based on period
    today = timezone.now().date()
    if period == 'today':
        start_date = today
        end_date = today
    elif period == 'week':
        start_date = today - timedelta(days=7)
        end_date = today
    elif period == 'month':
        start_date = today - timedelta(days=30)
        end_date = today
    elif period == 'year':
        start_date = today - timedelta(days=365)
        end_date = today
    else:
        start_date = today
        end_date = today
    
    # Get delivery statistics based on user role
    if user.role == 'customer':
        deliveries = DeliveryRequest.objects.filter(
            customer=user,
            created_at__date__range=[start_date, end_date]
        )
    else:  # driver
        deliveries = DeliveryRequest.objects.filter(
            driver=user,
            created_at__date__range=[start_date, end_date]
        )
    
    total_deliveries = deliveries.count()
    completed_deliveries = deliveries.filter(status='completed').count()
    pending_deliveries = deliveries.filter(status='pending').count()
    in_progress_deliveries = deliveries.filter(status='in_progress').count()
    
    # Mock statistics (in real implementation, these would be calculated)
    total_distance = "450 km"
    total_earnings = 1250.50
    average_rating = 4.8
    on_time_delivery_rate = 95.5
    
    return Response({
        'success': True,
        'data': {
            'totalDeliveries': total_deliveries,
            'completedDeliveries': completed_deliveries,
            'pendingDeliveries': pending_deliveries,
            'inProgressDeliveries': in_progress_deliveries,
            'totalDistance': total_distance,
            'totalEarnings': total_earnings,
            'averageRating': average_rating,
            'onTimeDeliveryRate': on_time_delivery_rate
        }
    })


@extend_schema(
    tags=['statistics'],
    summary='Get Driver Statistics',
    description='Retrieve detailed delivery statistics for the current driver.',
    parameters=[
        OpenApiParameter(name='period', description='Time period (today, week, month, all)', required=False, type=str),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'totalDeliveries': {'type': 'integer'},
                        'completedDeliveries': {'type': 'integer'},
                        'pendingDeliveries': {'type': 'integer'},
                        'inProgressDeliveries': {'type': 'integer'},
                        'assignedDeliveries': {'type': 'integer'},
                        'todayCompleted': {'type': 'integer'},
                        'todayPending': {'type': 'integer'},
                        'weekCompleted': {'type': 'integer'},
                        'monthCompleted': {'type': 'integer'},
                        'totalEarnings': {'type': 'number'},
                        'averageRating': {'type': 'number'},
                        'onTimeDeliveryRate': {'type': 'number'},
                        'period': {'type': 'string'}
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsDriver])
def driver_statistics_view(request):
    """
    Get detailed statistics for the current driver.
    """
    driver = request.user
    period = request.query_params.get('period', 'all')
    
    # Calculate date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Base queryset for this driver
    driver_deliveries = DeliveryRequest.objects.filter(driver=driver)
    
    # Filter by period if specified
    if period == 'today':
        deliveries = driver_deliveries.filter(created_at__date=today)
    elif period == 'week':
        deliveries = driver_deliveries.filter(created_at__date__gte=week_ago)
    elif period == 'month':
        deliveries = driver_deliveries.filter(created_at__date__gte=month_ago)
    else:  # 'all' or default
        deliveries = driver_deliveries
    
    # Calculate statistics
    total_deliveries = deliveries.count()
    completed_deliveries = deliveries.filter(status='completed').count()
    pending_deliveries = deliveries.filter(status='pending').count()
    in_progress_deliveries = deliveries.filter(status='in_progress').count()
    assigned_deliveries = deliveries.filter(status='assigned').count()
    
    # Today's statistics
    today_deliveries = driver_deliveries.filter(created_at__date=today)
    today_completed = today_deliveries.filter(status='completed').count()
    today_pending = today_deliveries.filter(status__in=['pending', 'assigned']).count()
    
    # Weekly and monthly completed
    week_completed = driver_deliveries.filter(
        status='completed',
        created_at__date__gte=week_ago
    ).count()
    
    month_completed = driver_deliveries.filter(
        status='completed',
        created_at__date__gte=month_ago
    ).count()
    
    # Calculate mock earnings (in real implementation, this would be based on actual pricing)
    earnings_per_delivery = 25.0  # Mock amount
    total_earnings = completed_deliveries * earnings_per_delivery
    
    # Calculate mock rating and on-time rate
    average_rating = 4.5 + (completed_deliveries * 0.01)  # Simple calculation
    on_time_delivery_rate = 95.0 + (completed_deliveries * 0.1)  # Mock calculation
    
    # Ensure rating doesn't exceed 5.0
    average_rating = min(average_rating, 5.0)
    on_time_delivery_rate = min(on_time_delivery_rate, 100.0)
    
    return Response({
        'success': True,
        'data': {
            'totalDeliveries': total_deliveries,
            'completedDeliveries': completed_deliveries,
            'pendingDeliveries': pending_deliveries,
            'inProgressDeliveries': in_progress_deliveries,
            'assignedDeliveries': assigned_deliveries,
            'todayCompleted': today_completed,
            'todayPending': today_pending,
            'weekCompleted': week_completed,
            'monthCompleted': month_completed,
            'totalEarnings': round(total_earnings, 2),
            'averageRating': round(average_rating, 1),
            'onTimeDeliveryRate': round(on_time_delivery_rate, 1),
            'period': period
        }
    })


@extend_schema(
    tags=['statistics'],
    summary='Get Customer Statistics',
    description='Retrieve detailed delivery statistics for the current customer.',
    parameters=[
        OpenApiParameter(name='period', description='Time period (today, week, month, all)', required=False, type=str),
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'totalDeliveries': {'type': 'integer'},
                        'completedDeliveries': {'type': 'integer'},
                        'pendingDeliveries': {'type': 'integer'},
                        'inProgressDeliveries': {'type': 'integer'},
                        'cancelledDeliveries': {'type': 'integer'},
                        'todayCompleted': {'type': 'integer'},
                        'todayPending': {'type': 'integer'},
                        'weekCompleted': {'type': 'integer'},
                        'monthCompleted': {'type': 'integer'},
                        'averageDeliveryTime': {'type': 'string'},
                        'totalSpent': {'type': 'number'},
                        'period': {'type': 'string'}
                    }
                }
            }
        }
    }
)
@api_view(['GET'])
@permission_classes([IsCustomer])
def customer_statistics_view(request):
    """
    Get detailed statistics for the current customer.
    """
    customer = request.user
    period = request.query_params.get('period', 'all')
    
    # Calculate date ranges
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Base queryset for this customer
    customer_deliveries = DeliveryRequest.objects.filter(customer=customer)
    
    # Filter by period if specified
    if period == 'today':
        deliveries = customer_deliveries.filter(created_at__date=today)
    elif period == 'week':
        deliveries = customer_deliveries.filter(created_at__date__gte=week_ago)
    elif period == 'month':
        deliveries = customer_deliveries.filter(created_at__date__gte=month_ago)
    else:  # 'all' or default
        deliveries = customer_deliveries
    
    # Calculate statistics
    total_deliveries = deliveries.count()
    completed_deliveries = deliveries.filter(status='completed').count()
    pending_deliveries = deliveries.filter(status='pending').count()
    in_progress_deliveries = deliveries.filter(status='in_progress').count()
    cancelled_deliveries = deliveries.filter(status='cancelled').count()
    
    # Today's statistics
    today_deliveries = customer_deliveries.filter(created_at__date=today)
    today_completed = today_deliveries.filter(status='completed').count()
    today_pending = today_deliveries.filter(status='pending').count()
    
    # Weekly and monthly completed
    week_completed = customer_deliveries.filter(
        status='completed',
        created_at__date__gte=week_ago
    ).count()
    
    month_completed = customer_deliveries.filter(
        status='completed',
        created_at__date__gte=month_ago
    ).count()
    
    # Calculate average delivery time (mock calculation)
    completed_deliveries_with_time = customer_deliveries.filter(
        status='completed',
        updated_at__isnull=False
    )
    
    if completed_deliveries_with_time.exists():
        # Mock average delivery time calculation
        avg_hours = 2.5 + (completed_deliveries * 0.1)  # Mock calculation
        average_delivery_time = f"{avg_hours:.1f} hours"
    else:
        average_delivery_time = "N/A"
    
    # Calculate total spent (mock calculation)
    base_delivery_cost = 15.0  # Mock base cost
    total_spent = completed_deliveries * base_delivery_cost
    
    return Response({
        'success': True,
        'data': {
            'totalDeliveries': total_deliveries,
            'completedDeliveries': completed_deliveries,
            'pendingDeliveries': pending_deliveries,
            'inProgressDeliveries': in_progress_deliveries,
            'cancelledDeliveries': cancelled_deliveries,
            'todayCompleted': today_completed,
            'todayPending': today_pending,
            'weekCompleted': week_completed,
            'monthCompleted': month_completed,
            'averageDeliveryTime': average_delivery_time,
            'totalSpent': round(total_spent, 2),
            'period': period
        }
    })


@extend_schema(
    tags=['debug'],
    summary='Debug - List All Delivery Requests',
    description='Debug endpoint to view all delivery requests in the database.',
    responses={200: DeliveryRequestSerializer}
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def debug_list_all_requests(request):
    """
    Debug endpoint to list all delivery requests.
    """
    if request.user.role != 'admin':
        return Response({
            'success': False,
            'error': 'Only admins can access this endpoint'
        }, status=status.HTTP_403_FORBIDDEN)
    
    all_requests = DeliveryRequest.objects.all().order_by('-id')
    serializer = DeliveryRequestSerializer(all_requests, many=True)
    
    return Response({
        'success': True,
        'data': {
            'total_count': all_requests.count(),
            'requests': serializer.data
        }
    }) 