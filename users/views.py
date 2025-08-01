"""
Views for user authentication and profile management.
"""
from rest_framework import status, generics
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from django.contrib.auth import authenticate
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiExample
from .models import User
from .serializers import (
    CustomTokenObtainPairSerializer,
    UserRegistrationSerializer,
    UserProfileSerializer,
    UserProfileUpdateSerializer,
)


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token obtain pair view with additional user data.
    """
    serializer_class = CustomTokenObtainPairSerializer
    
    @extend_schema(
        tags=['auth'],
        summary='Get JWT Token',
        description='Get JWT access , refresh token.',
        responses={200: CustomTokenObtainPairSerializer}
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


class UserRegistrationView(generics.CreateAPIView):
    """
    View for user registration.
    """
    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]
    
    @extend_schema(
        tags=['auth'],
        summary='Register New User',
        description='Create a new user account with email, password, and basic information. Role can be either "driver" or "customer".',
        examples=[
            OpenApiExample(
                'Driver Registration',
                value={
                    'email': 'driver@example.com',
                    'username': 'driver123',
                    'first_name': 'John',
                    'last_name': 'Driver',
                    'phone': '+1234567890',
                    'register_as': 'driver',
                    'password': 'password123',
                    'password_confirm': 'password123'
                }
            ),
            OpenApiExample(
                'Customer Registration',
                value={
                    'email': 'customer@example.com',
                    'username': 'customer123',
                    'first_name': 'Jane',
                    'last_name': 'Customer',
                    'phone': '+1234567891',
                    'register_as': 'customer',
                    'password': 'password123',
                    'password_confirm': 'password123'
                }
            )
        ],
        responses={201: UserRegistrationSerializer}
    )
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens for the new user
        token_serializer = CustomTokenObtainPairSerializer()
        token_data = token_serializer.get_token(user)
        
        return Response({
            'success': True,
            'data': {
                'token': str(token_data.access_token),
                'user': {
                    'id': user.id,
                    'name': user.full_name,
                    'email': user.email,
                    'phone': user.phone,
                    'role': user.role,
                }
            }
        }, status=status.HTTP_201_CREATED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    View for user profile retrieval and update.
    """
    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_object(self):
        return self.request.user
    
    def get_serializer_class(self):
        if self.request.method == 'PATCH':
            return UserProfileUpdateSerializer
        return UserProfileSerializer
    
    @extend_schema(
        tags=['auth'],
        summary='Get User Profile',
        description='Retrieve the current user\'s profile information.',
        responses={200: UserProfileSerializer}
    )
    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @extend_schema(
        tags=['auth'],
        summary='Update User Profile',
        description='Update the current user\'s profile information.',
        request=UserProfileUpdateSerializer,
        responses={200: UserProfileSerializer}
    )
    def update(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            'success': True,
            'data': {
                'id': user.id,
                'name': user.full_name,
                'phone': user.phone,
                'updatedAt': user.date_joined,
            }
        })


@extend_schema(
    tags=['auth'],
    summary='User Login',
    description='Authenticate a user with email and password to receive JWT tokens.',
    examples=[
        OpenApiExample(
            'Driver Login',
            value={
                'email': 'driver@example.com',
                'password': 'password123'
            }
        )
    ],
    responses={
        200: {
            'type': 'object',
            'properties': {
                'success': {'type': 'boolean'},
                'data': {
                    'type': 'object',
                    'properties': {
                        'token': {'type': 'string'},
                        'user': {
                            'type': 'object',
                            'properties': {
                                'id': {'type': 'integer'},
                                'name': {'type': 'string'},
                                'email': {'type': 'string'},
                                'phone': {'type': 'string'},
                                'role': {'type': 'string'}
                            }
                        }
                    }
                }
            }
        }
    }
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    Custom login view.
    """
    email = request.data.get('email')
    password = request.data.get('password')
    
    if not email or not password:
        return Response({
            'success': False,
            'error': {
                'code': 'VALIDATION_ERROR',
                'message': 'Email and password are required'
            }
        }, status=status.HTTP_400_BAD_REQUEST)
    
    user = authenticate(username=email, password=password)
    
    if not user:
        return Response({
            'success': False,
            'error': {
                'code': 'UNAUTHORIZED',
                'message': 'Invalid credentials'
            }
        }, status=status.HTTP_401_UNAUTHORIZED)
    
    # Generate tokens
    token_serializer = CustomTokenObtainPairSerializer()
    token_data = token_serializer.get_token(user)
    
    return Response({
        'success': True,
        'data': {
            'token': str(token_data.access_token),
            'user': {
                'id': user.id,
                'name': user.full_name,
                'email': user.email,
                'phone': user.phone,
                'role': user.role,
            }
        }
    }) 