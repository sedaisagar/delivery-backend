# Delivery Backend API

A Django REST API for managing delivery requests, routes, and driver operations.

## Features

- **Authentication**: JWT-based authentication with user roles (driver, admin, customer)
- **Delivery Management**: CRUD operations for delivery requests with role-based access
- **Route Calculation**: Directions and route information
- **Offline Sync**: Support for offline operations with sync endpoints
- **Statistics**: Comprehensive delivery statistics for drivers and customers
- **User Management**: User profiles and role-based access control
- **Driver Assignment**: Admin can assign drivers to delivery requests
- **Pagination**: Optimized pagination with configurable page sizes (max 10 items)
- **Search & Filtering**: Advanced search and filtering capabilities
- **API Documentation**: Auto-generated OpenAPI documentation with drf-spectacular

## Tech Stack

- **Framework**: Django 5.0+
- **API**: Django REST Framework
- **Authentication**: JWT (djangorestframework-simplejwt)
- **Database**: PostgreSQL
- **CORS**: django-cors-headers
- **Filtering**: django-filter
- **Documentation**: drf-spectacular

## Project Structure

```
delivery-backend/
├── delivery_backend/          # Main Django project
│   ├── __init__.py
│   ├── settings.py           # Django settings
│   ├── urls.py              # Main URL configuration
│   ├── wsgi.py              # WSGI application
│   └── asgi.py              # ASGI application
├── users/                    # User management app
│   ├── models.py            # Custom User model
│   ├── serializers.py       # User serializers
│   ├── views.py             # Authentication views
│   ├── urls.py              # User URLs
│   └── admin.py             # Admin configuration
├── delivery/                 # Delivery management app
│   ├── models.py            # Delivery models
│   ├── serializers.py       # Delivery serializers
│   ├── views.py             # Delivery views
│   ├── urls.py              # Delivery URLs
│   └── admin.py             # Admin configuration
├── requirements.txt          # Python dependencies
├── manage.py                # Django management script
├── env.example              # Environment variables example
└── README.md               # This file
```

## Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd delivery-backend
   ```

2. **Create and activate virtual environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   ```bash
   cp env.example .env
   # Edit .env with your configuration
   ```

5. **Set up database**
   ```bash
   # Create PostgreSQL database
   createdb delivery_db
   
   # Run migrations
   python manage.py makemigrations
   python manage.py migrate
   ```

6. **Create superuser**
   ```bash
   python manage.py createsuperuser
   ```

7. **Run the development server**
   ```bash
   python manage.py runserver
   ```

## API Documentation

The API documentation is automatically generated using drf-spectacular and is available at:

- **Swagger UI**: http://localhost:8000/api/docs/
- **ReDoc**: http://localhost:8000/api/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

### API Groups

The API is organized into the following groups:

- **auth**: User authentication, registration, and profile management
- **delivery-requests**: CRUD operations for delivery requests with role-based access
- **partners**: Available delivery partners (drivers) for assignment
- **directions**: Route calculation and directions
- **sync**: Offline sync operations for mobile apps
- **statistics**: Comprehensive delivery statistics for drivers and customers
- **debug**: Debug endpoints for development (admin only)

## API Endpoints

### Authentication (`/api/v1/auth/`)
- `POST /login/` - User login
- `POST /register/` - User registration
- `POST /refresh/` - Refresh JWT token
- `GET /profile/` - Get user profile
- `PATCH /profile/` - Update user profile

### Delivery Requests (`/api/v1/delivery-requests/`)
- `GET /` - List delivery requests (role-based filtering)
- `POST /` - Create delivery request (customers only)
- `GET /{id}/` - Get delivery request (owner or admin)
- `PATCH /{id}/` - Update delivery request (owner or admin)
- `DELETE /{id}/` - Delete delivery request (owner or admin)
- `GET /assigned/` - Get assigned delivery requests (drivers only)

### Partners (`/api/v1/partners/`)
- `GET /` - Get available delivery partners (drivers)

### Directions (`/api/v1/directions/`)
- `GET /` - Get route directions (mobile app only)

### Sync (`/api/v1/sync/`)
- `POST /pending/` - Sync pending requests (mobile app only)
- `GET /status/` - Get sync status (mobile app only)

### Statistics (`/api/v1/statistics/`)
- `GET /` - Get general delivery statistics (mobile app only)
- `GET /driver/` - Get driver-specific statistics (drivers only)
- `GET /customer/` - Get customer-specific statistics (customers only)

### Debug (`/api/v1/debug/`)
- `GET /requests/` - List all delivery requests (admin only)

## Environment Variables

Create a `.env` file with the following variables:

```env
# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1

# Database Settings
DB_NAME=delivery_db
DB_USER=postgres
DB_PASSWORD=your-db-password
DB_HOST=localhost
DB_PORT=5432

# JWT Settings
JWT_SECRET_KEY=your-jwt-secret-key-here

# CORS Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://127.0.0.1:3000
```

## API Documentation

The API follows RESTful conventions and returns JSON responses in the following format:

### Success Response
```json
{
  "success": true,
  "data": {
    // Response data
  }
}
```

### Error Response
```json
{
  "success": false,
  "error": {
    "code": "ERROR_CODE",
    "message": "Error message",
    "details": {
      // Additional error details
    }
  }
}
```

## Authentication

All API endpoints (except login and register) require JWT authentication. Include the token in the Authorization header:

```
Authorization: Bearer <your-jwt-token>
```

## Development

### Running Tests
```bash
python manage.py test
```

### Code Formatting
```bash
black .
```

### Linting
```bash
flake8 .
```

### Creating Migrations
```bash
python manage.py makemigrations
```

### Applying Migrations
```bash
python manage.py migrate
```

### Generating API Schema
```bash
python manage.py spectacular --file schema.yml
```

## Deployment

1. Set `DEBUG=False` in production
2. Use a proper database (PostgreSQL recommended)
3. Set up static file serving
4. Configure CORS for your frontend domain
5. Use environment variables for sensitive settings

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

This project is licensed under the MIT License. 