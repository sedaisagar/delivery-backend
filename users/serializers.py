"""
Serializers for user authentication and profile management.
"""
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import authenticate
from .models import User


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    Custom token serializer with additional user data.
    """
    def validate(self, attrs):
        data = super().validate(attrs)
        
        # Add user data to response
        user = self.user
        data['user'] = {
            'id': user.id,
            'name': user.full_name,
            'email': user.email,
            'phone': user.phone,
            'role': user.role,
        }
        
        return data


class UserRegistrationSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.
    """
    password = serializers.CharField(write_only=True)
    password_confirm = serializers.CharField(write_only=True)
    register_as = serializers.ChoiceField(choices=[('driver', 'Driver'), ('customer', 'Customer')],write_only=True)
    
    class Meta:
        model = User
        fields = ['email', 'username', 'first_name', 'last_name', 'phone', 'register_as', 'password', 'password_confirm']
        extra_kwargs = {
            'password': {'write_only': True},
            'password_confirm': {'write_only': True},
        }
    
    def validate(self, attrs):
        super().validate(attrs)
        register_as = attrs.pop('register_as')
        if attrs['password'] != attrs['password_confirm']:
            raise serializers.ValidationError("Passwords don't match")
        if register_as == 'driver':
            attrs['role'] = 'driver'
        else:
            attrs['role'] = 'customer'
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Serializer for user profile.
    """
    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'phone', 'role', 'avatar']
        read_only_fields = ['id', 'email', 'role']


class UserProfileUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    """
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'phone', 'avatar'] 