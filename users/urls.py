"""
URL patterns for user authentication.
"""
from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    UserRegistrationView,
    UserProfileView,
    login_view,
)

urlpatterns = [
    path('login/', CustomTokenObtainPairView.as_view(), name='login'),
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', UserProfileView.as_view(), name='profile'),
] 