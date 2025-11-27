from django.contrib import admin
from .models import Interview, InterviewQuestion, InterviewFeedback


@admin.register(Interview)
class InterviewAdmin(admin.ModelAdmin):
    list_display = ['application', 'interview_type', 'status', 'scheduled_at', 'ai_score']
    list_filter = ['status', 'interview_type', 'scheduled_at']
    search_fields = ['application__user__username', 'application__job__title']
    readonly_fields = ['ai_score', 'ai_analyzed_at']


@admin.register(InterviewQuestion)
class InterviewQuestionAdmin(admin.ModelAdmin):
    list_display = ['interview', 'question_text', 'ai_score', 'order']
    list_filter = ['interview__status']


@admin.register(InterviewFeedback)
class InterviewFeedbackAdmin(admin.ModelAdmin):
    list_display = ['interview', 'rating', 'created_at']
    list_filter = ['rating', 'created_at']