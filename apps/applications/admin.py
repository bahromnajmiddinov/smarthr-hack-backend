from django.contrib import admin
from .models import Application, ApplicationNote, ApplicationStatusHistory


@admin.register(Application)
class ApplicationAdmin(admin.ModelAdmin):
    list_display = ['user', 'job', 'status', 'ai_match_score', 'submitted_at']
    list_filter = ['status', 'submitted_at']
    search_fields = ['user__username', 'job__title']
    readonly_fields = ['ai_match_score', 'ai_analyzed_at', 'submitted_at']


@admin.register(ApplicationNote)
class ApplicationNoteAdmin(admin.ModelAdmin):
    list_display = ['application', 'author', 'created_at']
    list_filter = ['created_at']
    search_fields = ['content', 'application__user__username']


@admin.register(ApplicationStatusHistory)
class ApplicationStatusHistoryAdmin(admin.ModelAdmin):
    list_display = ['application', 'old_status', 'new_status', 'changed_by', 'changed_at']
    list_filter = ['old_status', 'new_status', 'changed_at']
