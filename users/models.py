"""
Custom User model for the delivery app.
"""
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """
    Custom User model with additional fields for delivery app.
    """
    ROLE_CHOICES = [
        ('driver', 'Driver'),
        ('admin', 'Admin'),
        ('customer', 'Customer'),
    ]
    
    email = models.EmailField(_('email address'), unique=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    
    # Use email as username
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    class Meta:
        db_table = "users"
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return self.email
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip() or self.email 