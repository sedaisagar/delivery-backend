"""
Custom permission classes for role-based access control.
"""
from rest_framework import permissions


class IsCustomer(permissions.BasePermission):
    """
    Permission to check if user is a customer.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'customer'


class IsDriver(permissions.BasePermission):
    """
    Permission to check if user is a driver.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'driver'


class IsAdmin(permissions.BasePermission):
    """
    Permission to check if user is an admin.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == 'admin'


class IsCustomerOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is a customer or admin.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['customer', 'admin']


class IsDriverOrAdmin(permissions.BasePermission):
    """
    Permission to check if user is a driver or admin.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in ['driver', 'admin']


class IsOwnerOrAdmin(permissions.BasePermission):
    """
    Permission to check if user owns the object or is admin.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access everything
        if request.user.role == 'admin':
            return True
        
        # Customer can only access their own requests
        if request.user.role == 'customer':
            return obj.customer == request.user
        
        # Driver can only access their assigned requests
        if request.user.role == 'driver':
            return obj.driver == request.user
        
        return False


class MobileAppPermission(permissions.BasePermission):
    """
    Permission to block admin access to mobile app endpoints.
    """
    def has_permission(self, request, view):
        # Block admin access to mobile endpoints
        if request.user.role == 'admin':
            return False
        return request.user.is_authenticated 