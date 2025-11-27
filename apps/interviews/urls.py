from django.urls import path
from .views import (
    InterviewListView,
    InterviewCreateView,
    InterviewDetailView,
    InterviewUpdateView,
    InterviewCancelView,
    InterviewRescheduleView,
    VideoUploadView,
    InterviewQuestionsView,
    InterviewFeedbackView,
    InterviewStatsView,
    UpcomingInterviewsView,
)

app_name = 'interviews'

urlpatterns = [
    # Interview management
    path('', InterviewListView.as_view(), name='interview_list'),
    path('upcoming/', UpcomingInterviewsView.as_view(), name='upcoming_interviews'),
    path('create/', InterviewCreateView.as_view(), name='interview_create'),
    path('<uuid:pk>/', InterviewDetailView.as_view(), name='interview_detail'),
    path('<uuid:pk>/update/', InterviewUpdateView.as_view(), name='interview_update'),
    path('<uuid:pk>/cancel/', InterviewCancelView.as_view(), name='interview_cancel'),
    path('<uuid:pk>/reschedule/', InterviewRescheduleView.as_view(), name='interview_reschedule'),
    
    # Video
    path('<uuid:pk>/upload-video/', VideoUploadView.as_view(), name='video_upload'),
    
    # Questions
    path('<uuid:interview_id>/questions/', InterviewQuestionsView.as_view(), name='interview_questions'),
    
    # Feedback
    path('<uuid:interview_id>/feedback/', InterviewFeedbackView.as_view(), name='interview_feedback'),
    
    # Stats
    path('stats/', InterviewStatsView.as_view(), name='interview_stats'),
]