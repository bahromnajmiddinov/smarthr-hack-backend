from django.contrib import admin
from .models import Profile, CV, Certificate


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'location', 'ai_score', 'created_at']
    list_filter = ['created_at']
    search_fields = ['user__username', 'user__full_name', 'bio']
    readonly_fields = ['ai_score', 'ai_analyzed_at']


@admin.register(CV)
class CVAdmin(admin.ModelAdmin):
    list_display = ['profile', 'original_filename', 'ai_processed', 'uploaded_at']
    list_filter = ['ai_processed', 'uploaded_at']
    search_fields = ['profile__user__username', 'original_filename']


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ['profile', 'title', 'issuer', 'issue_date']
    list_filter = ['issue_date']
    search_fields = ['title', 'issuer', 'profile__user__username']
