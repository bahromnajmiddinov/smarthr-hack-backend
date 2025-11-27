from django.urls import path
from .views import (
    MyProfileView,
    ProfileDetailView,
    CVListView,
    CVUploadView,
    CVDeleteView,
    GenerateCVView,
    CertificateListCreateView,
    CertificateDetailView,
    ProfileStatsView,
    AnalyzeProfileView,
)

app_name = 'profiles'

urlpatterns = [
    # Profile
    path('me/', MyProfileView.as_view(), name='my_profile'),
    path('me/stats/', ProfileStatsView.as_view(), name='my_stats'),
    path('me/analyze/', AnalyzeProfileView.as_view(), name='analyze_profile'),
    path('<uuid:user_id>/', ProfileDetailView.as_view(), name='profile_detail'),
    
    # CV
    path('me/cvs/', CVListView.as_view(), name='cv_list'),
    path('me/cvs/upload/', CVUploadView.as_view(), name='cv_upload'),
    path('me/cvs/<int:pk>/', CVDeleteView.as_view(), name='cv_delete'),
    path('me/cvs/generate/', GenerateCVView.as_view(), name='cv_generate'),
    
    # Certificates
    path('me/certificates/', CertificateListCreateView.as_view(), name='certificate_list'),
    path('me/certificates/<int:pk>/', CertificateDetailView.as_view(), name='certificate_detail'),
]