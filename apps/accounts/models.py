from uuid import uuid4
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """Custom User model with role-based access"""
    
    ROLE_CHOICES = [
        ('candidate', 'Candidate'),
        ('employer', 'Employer'),
        ('gov', 'Government'),
        ('admin', 'Admin'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    full_name = models.CharField(_('full name'), max_length=255)
    phone = models.CharField(_('phone number'), max_length=20, unique=True, null=True, blank=True)
    email = models.EmailField(_('email address'), unique=True, null=True, blank=True)
    role = models.CharField(_('role'), max_length=20, choices=ROLE_CHOICES, default='candidate')
    is_phone_verified = models.BooleanField(_('phone verified'), default=False)
    is_email_verified = models.BooleanField(_('email verified'), default=False)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'users'
        ordering = ['-created_at']
        verbose_name = _('user')
        verbose_name_plural = _('users')
    
    def __str__(self):
        return f"{self.full_name} ({self.role})"
    
    @property
    def is_candidate(self):
        return self.role == 'candidate'
    
    @property
    def is_employer(self):
        return self.role == 'employer'
    
    @property
    def is_government(self):
        return self.role == 'gov'


class PhoneVerification(models.Model):
    """SMS verification codes"""
    
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='phone_verifications')
    phone = models.CharField(max_length=20)
    code = models.CharField(max_length=6)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    
    class Meta:
        db_table = 'phone_verifications'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.phone} - {self.code}"
    