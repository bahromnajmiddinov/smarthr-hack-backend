from django.urls import path
from .views import (
    JobListView,
    JobCreateView,
    JobDetailView,
    JobUpdateView,
    JobDeleteView,
    MyJobsView,
    JobStatsView,
    JobRecommendationsView,
    JobPublishView,
    JobCloseView,
)

app_name = 'jobs'

urlpatterns = [
    # Public job endpoints
    path('', JobListView.as_view(), name='job_list'),
    path('<uuid:pk>/', JobDetailView.as_view(), name='job_detail'),
    path('recommendations/', JobRecommendationsView.as_view(), name='job_recommendations'),
    
    # Employer job management
    path('create/', JobCreateView.as_view(), name='job_create'),
    path('<uuid:pk>/update/', JobUpdateView.as_view(), name='job_update'),
    path('<uuid:pk>/delete/', JobDeleteView.as_view(), name='job_delete'),
    path('<uuid:pk>/publish/', JobPublishView.as_view(), name='job_publish'),
    path('<uuid:pk>/close/', JobCloseView.as_view(), name='job_close'),
    
    # My jobs
    path('my/jobs/', MyJobsView.as_view(), name='my_jobs'),
    path('my/stats/', JobStatsView.as_view(), name='my_stats'),
]