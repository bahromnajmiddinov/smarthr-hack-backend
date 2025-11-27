from django.contrib import admin
from .models import Job, JobView


@admin.register(Job)
class JobAdmin(admin.ModelAdmin):
    list_display = ['title', 'employer', 'location', 'status', 'views_count', 'applications_count', 'created_at']
    list_filter = ['status', 'job_type', 'is_remote', 'created_at']
    search_fields = ['title', 'description', 'location', 'employer__full_name']
    readonly_fields = ['views_count', 'applications_count', 'created_at', 'updated_at']


@admin.register(JobView)
class JobViewAdmin(admin.ModelAdmin):
    list_display = ['job', 'user', 'ip_address', 'viewed_at']
    list_filter = ['viewed_at']
    search_fields = ['job__title', 'user__username']
