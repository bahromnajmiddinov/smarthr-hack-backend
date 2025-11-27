from django.urls import path
from .views import (
    ApplicationCreateView,
    MyApplicationsView,
    ApplicationDetailView,
    ApplicationWithdrawView,
    JobApplicationsView,
    ApplicationStatusUpdateView,
    ApplicationNoteCreateView,
    ApplicationNotesView,
    ShortlistCandidatesView,
    BulkStatusUpdateView,
)

app_name = 'applications'

urlpatterns = [
    # Candidate endpoints
    path('apply/', ApplicationCreateView.as_view(), name='application_create'),
    path('my/', MyApplicationsView.as_view(), name='my_applications'),
    path('<uuid:pk>/', ApplicationDetailView.as_view(), name='application_detail'),
    path('<uuid:pk>/withdraw/', ApplicationWithdrawView.as_view(), name='application_withdraw'),
    
    # Employer endpoints
    path('job/<uuid:job_id>/', JobApplicationsView.as_view(), name='job_applications'),
    path('job/<uuid:job_id>/shortlist/', ShortlistCandidatesView.as_view(), name='shortlist_candidates'),
    path('<uuid:pk>/status/', ApplicationStatusUpdateView.as_view(), name='application_status_update'),
    path('bulk/update/', BulkStatusUpdateView.as_view(), name='bulk_status_update'),
    
    # Notes
    path('<uuid:application_id>/notes/', ApplicationNotesView.as_view(), name='application_notes'),
    path('<uuid:application_id>/notes/create/', ApplicationNoteCreateView.as_view(), name='application_note_create'),
]