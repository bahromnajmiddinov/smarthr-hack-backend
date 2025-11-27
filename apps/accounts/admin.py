from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, PhoneVerification


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ['username', 'email', 'full_name', 'role', 'is_phone_verified', 'created_at']
    list_filter = ['role', 'is_phone_verified', 'is_active']
    search_fields = ['username', 'email', 'full_name', 'phone']
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('full_name', 'email', 'phone')}),
        ('Role & Verification', {'fields': ('role', 'is_phone_verified', 'is_email_verified')}),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(PhoneVerification)
class PhoneVerificationAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'code', 'is_verified', 'created_at']
    list_filter = ['is_verified']
    search_fields = ['phone', 'user__username']