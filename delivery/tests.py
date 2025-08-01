"""
Tests for delivery app functionality.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from .models import DeliveryRequest, SyncLog
from django.utils import timezone

User = get_user_model()


class DeliveryRequestModelTest(TestCase):
    """Test cases for DeliveryRequest model."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='driver'
        )
    
    def test_create_delivery_request(self):
        """Test creating a delivery request."""
        delivery = DeliveryRequest.objects.create(
            pickup_address='123 Main St',
            dropoff_address='456 Oak Ave',
            customer_name='John Doe',
            customer_phone='+1234567890',
            delivery_note='Test delivery',
            driver=self.user
        )
        
        self.assertEqual(delivery.status, 'pending')
        self.assertEqual(delivery.sync_status, 'synced')
        self.assertFalse(delivery.pending_sync)
    
    def test_offline_delivery_request(self):
        """Test creating an offline delivery request."""
        delivery = DeliveryRequest.objects.create(
            pickup_address='123 Main St',
            dropoff_address='456 Oak Ave',
            customer_name='John Doe',
            customer_phone='+1234567890',
            pending_sync=True,
            sync_status='pending'
        )
        
        self.assertTrue(delivery.pending_sync)
        self.assertEqual(delivery.sync_status, 'pending')
    
    def test_mark_as_synced(self):
        """Test marking a delivery request as synced."""
        delivery = DeliveryRequest.objects.create(
            pickup_address='123 Main St',
            dropoff_address='456 Oak Ave',
            customer_name='John Doe',
            customer_phone='+1234567890',
            pending_sync=True,
            sync_status='pending'
        )
        
        delivery.mark_as_synced()
        
        self.assertFalse(delivery.pending_sync)
        self.assertEqual(delivery.sync_status, 'synced')
        self.assertIsNotNone(delivery.synced_at)


class DeliveryRequestAPITest(APITestCase):
    """Test cases for delivery request API endpoints."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='driver'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_create_delivery_request(self):
        """Test creating a delivery request via API."""
        url = reverse('delivery-requests')
        data = {
            'pickup_address': '123 Main St',
            'dropoff_address': '456 Oak Ave',
            'customer_name': 'John Doe',
            'customer_phone': '+1234567890',
            'delivery_note': 'Test delivery',
            'pending_sync': False
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(DeliveryRequest.objects.count(), 1)
        
        delivery = DeliveryRequest.objects.first()
        self.assertEqual(delivery.customer_name, 'John Doe')
        self.assertEqual(delivery.sync_status, 'synced')
    
    def test_create_offline_delivery_request(self):
        """Test creating an offline delivery request via API."""
        url = reverse('delivery-requests')
        data = {
            'pickup_address': '123 Main St',
            'dropoff_address': '456 Oak Ave',
            'customer_name': 'John Doe',
            'customer_phone': '+1234567890',
            'delivery_note': 'Test offline delivery',
            'pending_sync': True
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        
        delivery = DeliveryRequest.objects.first()
        self.assertTrue(delivery.pending_sync)
        self.assertEqual(delivery.sync_status, 'pending')
    
    def test_list_delivery_requests(self):
        """Test listing delivery requests."""
        # Create test delivery requests
        DeliveryRequest.objects.create(
            pickup_address='123 Main St',
            dropoff_address='456 Oak Ave',
            customer_name='John Doe',
            customer_phone='+1234567890',
            driver=self.user
        )
        
        url = reverse('delivery-requests')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['requests']), 1)
    
    def test_update_delivery_request_status(self):
        """Test updating delivery request status."""
        delivery = DeliveryRequest.objects.create(
            pickup_address='123 Main St',
            dropoff_address='456 Oak Ave',
            customer_name='John Doe',
            customer_phone='+1234567890',
            driver=self.user
        )
        
        url = reverse('delivery-request-detail', args=[delivery.id])
        data = {'status': 'in_progress'}
        
        response = self.client.patch(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        delivery.refresh_from_db()
        self.assertEqual(delivery.status, 'in_progress')


class SyncAPITest(APITestCase):
    """Test cases for sync functionality."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='driver'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_sync_pending_requests(self):
        """Test syncing pending delivery requests."""
        # Create a pending delivery request
        delivery = DeliveryRequest.objects.create(
            pickup_address='123 Main St',
            dropoff_address='456 Oak Ave',
            customer_name='John Doe',
            customer_phone='+1234567890',
            pending_sync=True,
            sync_status='pending',
            driver=self.user
        )
        
        url = reverse('sync-pending')
        data = {
            'requests': [{
                'local_id': 'local_123',
                'pickup_address': '123 Main St',
                'dropoff_address': '456 Oak Ave',
                'customer_name': 'John Doe',
                'customer_phone': '+1234567890',
                'delivery_note': 'Updated note',
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
            }]
        }
        
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['data']['synced']), 1)
        
        # Check that sync log was created
        self.assertEqual(SyncLog.objects.count(), 1)
    
    def test_sync_status(self):
        """Test getting sync status."""
        # Create pending delivery requests
        DeliveryRequest.objects.create(
            pickup_address='123 Main St',
            dropoff_address='456 Oak Ave',
            customer_name='John Doe',
            customer_phone='+1234567890',
            pending_sync=True,
            sync_status='pending',
            driver=self.user
        )
        
        url = reverse('sync-status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['data']['pendingCount'], 1)


class PartnerAPITest(APITestCase):
    """Test cases for partner selection API."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123',
            role='admin'
        )
        self.client.force_authenticate(user=self.user)
    
    def test_get_available_partners(self):
        """Test getting available partners."""
        url = reverse('available-partners')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('data', response.data)
        self.assertIsInstance(response.data['data'], list)
        
        # Check that partners have required fields
        if response.data['data']:
            partner = response.data['data'][0]
            required_fields = ['id', 'name', 'email', 'phone', 'rating', 'distance', 'available']
            for field in required_fields:
                self.assertIn(field, partner) 