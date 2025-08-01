# Delivery App REST API Documentation

## Base URL
```
https://api.deliveryapp.com/v1
```

## Authentication
All endpoints require Bearer token authentication:
```
Authorization: Bearer <token>
```

---

## 1. Authentication Endpoints

### POST /auth/login
**Request:**
```json
{
  "email": "driver@example.com",
  "password": "password123"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
    "user": {
      "id": "user_123",
      "name": "John Driver",
      "email": "driver@example.com",
      "phone": "+1234567890",
      "role": "driver"
    }
  }
}
```

### POST /auth/refresh
**Request:**
```json
{
  "refreshToken": "refresh_token_here"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "token": "new_access_token",
    "refreshToken": "new_refresh_token"
  }
}
```

---

## 2. Delivery Requests Endpoints

### GET /delivery-requests
**Query Parameters:**
- `status` (optional): `pending`, `in_progress`, `completed`, `cancelled`
- `page` (optional): Page number (default: 1)
- `limit` (optional): Items per page (default: 20)
- `sort` (optional): `created_at`, `updated_at`, `status`

**Response:**
```json
{
  "success": true,
  "data": {
    "requests": [
      {
        "id": "req_123",
        "pickupAddress": "123 Main St, City",
        "dropoffAddress": "456 Oak Ave, Town",
        "customerName": "John Doe",
        "customerPhone": "+1234567890",
        "deliveryNote": "Please ring doorbell",
        "status": "pending",
        "syncStatus": "synced",
        "createdAt": "2024-01-15T10:30:00Z",
        "updatedAt": "2024-01-15T10:30:00Z",
        "coordinates": {
          "pickup": {
            "latitude": 37.78825,
            "longitude": -122.4324
          },
          "dropoff": {
            "latitude": 37.78925,
            "longitude": -122.4344
          }
        }
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 45,
      "totalPages": 3
    }
  }
}
```

### POST /delivery-requests
**Request:**
```json
{
  "pickupAddress": "123 Main St, City",
  "dropoffAddress": "456 Oak Ave, Town",
  "customerName": "John Doe",
  "customerPhone": "+1234567890",
  "deliveryNote": "Please ring doorbell",
  "coordinates": {
    "pickup": {
      "latitude": 37.78825,
      "longitude": -122.4324
    },
    "dropoff": {
      "latitude": 37.78925,
      "longitude": -122.4344
    }
  }
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "req_123",
    "pickupAddress": "123 Main St, City",
    "dropoffAddress": "456 Oak Ave, Town",
    "customerName": "John Doe",
    "customerPhone": "+1234567890",
    "deliveryNote": "Please ring doorbell",
    "status": "pending",
    "syncStatus": "synced",
    "createdAt": "2024-01-15T10:30:00Z",
    "coordinates": {
      "pickup": {
        "latitude": 37.78825,
        "longitude": -122.4324
      },
      "dropoff": {
        "latitude": 37.78925,
        "longitude": -122.4344
      }
    }
  }
}
```

### GET /delivery-requests/{id}
**Response:**
```json
{
  "success": true,
  "data": {
    "id": "req_123",
    "pickupAddress": "123 Main St, City",
    "dropoffAddress": "456 Oak Ave, Town",
    "customerName": "John Doe",
    "customerPhone": "+1234567890",
    "deliveryNote": "Please ring doorbell",
    "status": "pending",
    "syncStatus": "synced",
    "createdAt": "2024-01-15T10:30:00Z",
    "updatedAt": "2024-01-15T10:30:00Z",
    "coordinates": {
      "pickup": {
        "latitude": 37.78825,
        "longitude": -122.4324
      },
      "dropoff": {
        "latitude": 37.78925,
        "longitude": -122.4344
      }
    }
  }
}
```

### PATCH /delivery-requests/{id}
**Request:**
```json
{
  "status": "in_progress"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "req_123",
    "status": "in_progress",
    "updatedAt": "2024-01-15T11:00:00Z"
  }
}
```

### DELETE /delivery-requests/{id}
**Response:**
```json
{
  "success": true,
  "message": "Delivery request deleted successfully"
}
```

---

## 3. Route & Directions Endpoints

### GET /directions
**Query Parameters:**
- `pickup_lat`: Pickup latitude
- `pickup_lng`: Pickup longitude
- `dropoff_lat`: Dropoff latitude
- `dropoff_lng`: Dropoff longitude
- `mode` (optional): `driving`, `walking`, `bicycling` (default: driving)

**Response:**
```json
{
  "success": true,
  "data": {
    "route": {
      "points": [
        {"latitude": 37.78825, "longitude": -122.4324},
        {"latitude": 37.78850, "longitude": -122.4328},
        {"latitude": 37.78925, "longitude": -122.4344}
      ],
      "distance": "2.5 km",
      "duration": "8 mins",
      "polyline": "encoded_polyline_string"
    }
  }
}
```

---

## 4. Sync Endpoints

### POST /sync/pending
**Request:**
```json
{
  "requests": [
    {
      "id": "local_123",
      "pickupAddress": "123 Main St, City",
      "dropoffAddress": "456 Oak Ave, Town",
      "customerName": "John Doe",
      "customerPhone": "+1234567890",
      "deliveryNote": "Please ring doorbell",
      "status": "pending",
      "createdAt": "2024-01-15T10:30:00Z",
      "coordinates": {
        "pickup": {
          "latitude": 37.78825,
          "longitude": -122.4324
        },
        "dropoff": {
          "latitude": 37.78925,
          "longitude": -122.4344
        }
      }
    }
  ]
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "synced": [
      {
        "localId": "local_123",
        "serverId": "req_456",
        "status": "synced"
      }
    ],
    "failed": [],
    "conflicts": []
  }
}
```

### GET /sync/status
**Response:**
```json
{
  "success": true,
  "data": {
    "lastSync": "2024-01-15T10:30:00Z",
    "pendingCount": 5,
    "failedCount": 0,
    "syncedCount": 25
  }
}
```

---

## 5. User Profile Endpoints

### GET /profile
**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "name": "John Driver",
    "email": "driver@example.com",
    "phone": "+1234567890",
    "role": "driver",
    "avatar": "https://api.deliveryapp.com/avatars/user_123.jpg",
    "createdAt": "2024-01-01T00:00:00Z"
  }
}
```

### PATCH /profile
**Request:**
```json
{
  "name": "John Updated",
  "phone": "+1234567891"
}
```

**Response:**
```json
{
  "success": true,
  "data": {
    "id": "user_123",
    "name": "John Updated",
    "phone": "+1234567891",
    "updatedAt": "2024-01-15T12:00:00Z"
  }
}
```

---

## 6. Statistics Endpoints

### GET /statistics
**Query Parameters:**
- `period` (optional): `today`, `week`, `month`, `year` (default: today)

**Response:**
```json
{
  "success": true,
  "data": {
    "totalDeliveries": 150,
    "completedDeliveries": 120,
    "pendingDeliveries": 20,
    "inProgressDeliveries": 10,
    "totalDistance": "450 km",
    "totalEarnings": 1250.50,
    "averageRating": 4.8,
    "onTimeDeliveryRate": 95.5
  }
}
```

---

## Error Responses

All endpoints return consistent error responses:

```json
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request data",
    "details": {
      "pickupAddress": "Pickup address is required"
    }
  }
}
```

Common error codes:
- `UNAUTHORIZED`: Invalid or missing token
- `FORBIDDEN`: Insufficient permissions
- `NOT_FOUND`: Resource not found
- `VALIDATION_ERROR`: Invalid request data
- `CONFLICT`: Resource conflict
- `INTERNAL_ERROR`: Server error

---

## Implementation Notes

1. **Offline Support**: The API should handle offline scenarios gracefully with sync endpoints
2. **Real-time Updates**: Consider WebSocket connections for real-time status updates
3. **Rate Limiting**: Implement rate limiting for API endpoints
4. **Caching**: Use ETags and caching headers for better performance
5. **Pagination**: All list endpoints support pagination
6. **Filtering**: Support filtering by status, date ranges, etc.
7. **Search**: Implement search functionality for delivery requests

This API design covers all the workflows in your delivery app including authentication, CRUD operations for delivery requests, route calculations, offline sync, user management, and statistics. 