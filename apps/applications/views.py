from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Q

from .models import Application, ApplicationNote, ApplicationStatusHistory
from .serializers import (
    ApplicationSerializer,
    ApplicationCreateSerializer,
    ApplicationListSerializer,
    ApplicationStatusUpdateSerializer,
    ApplicationNoteSerializer,
    ApplicationDetailSerializer
)
from apps.jobs.models import Job
from apps.common.permissions import IsEmployer
from .tasks import calculate_ai_match_score
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter


@extend_schema(
    summary="Submit application for a job",
    description="Create an application for a job; accepts job_id, cover_letter, and optional cv file.",
    request=ApplicationCreateSerializer,
    responses={201: OpenApiResponse(description='Created application')},
    tags=["Applications"]
)
class ApplicationCreateView(generics.CreateAPIView):
    """Apply to a job"""
    
    serializer_class = ApplicationCreateSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        job_id = serializer.validated_data.pop('job_id')
        job = get_object_or_404(Job, id=job_id)
        
        application = serializer.save(
            user=self.request.user,
            job=job
        )
        
        # Increment job application count
        job.applications_count += 1
        job.save(update_fields=['applications_count'])
        
        # Trigger AI matching
        calculate_ai_match_score.delay(application.id)
        
        return application


@extend_schema(
    summary="List my applications",
    description="Returns applications belonging to the authenticated user. Supports optional ?status= filter",
    parameters=[OpenApiParameter(name='status', description='Filter by application status', required=False, type=str)],
    responses={200: ApplicationListSerializer(many=True)},
    tags=["Applications"]
)
class MyApplicationsView(generics.ListAPIView):
    """List applications by current user"""
    
    serializer_class = ApplicationListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        queryset = Application.objects.filter(user=self.request.user)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset.order_by('-submitted_at')


@extend_schema(
    summary="Get application details",
    description="Retrieve a detailed view of an application. Employers can view applications for their jobs; candidates can view their own.",
    responses={200: ApplicationDetailSerializer},
    tags=["Applications"]
)
class ApplicationDetailView(generics.RetrieveAPIView):
    """Get application details"""
    
    serializer_class = ApplicationDetailSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        # Candidates can see their own applications
        # Employers can see applications to their jobs
        if user.is_employer:
            return Application.objects.filter(job__employer=user)
        else:
            return Application.objects.filter(user=user)


@extend_schema(
    summary="Withdraw an application",
    description="Allows candidate to withdraw an application if it is not accepted/rejected/withdrawn already.",
    responses={200: OpenApiResponse(description='Confirmation message'), 400: OpenApiResponse(description='Error')},
    tags=["Applications"]
)
class ApplicationWithdrawView(views.APIView):
    """Withdraw application"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        application = get_object_or_404(
            Application,
            pk=pk,
            user=request.user
        )
        
        if application.status in ['accepted', 'rejected', 'withdrawn']:
            return Response(
                {'error': 'Cannot withdraw this application'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        old_status = application.status
        application.status = 'withdrawn'
        application.save()
        
        # Create status history
        ApplicationStatusHistory.objects.create(
            application=application,
            old_status=old_status,
            new_status='withdrawn',
            changed_by=request.user,
            comment='Application withdrawn by candidate'
        )
        
        return Response({
            'message': 'Application withdrawn successfully'
        })


@extend_schema(
    summary="List applications for a job (employer)",
    description="Returns applications for a job. Supports `status` and `sort` query params.",
    parameters=[
        OpenApiParameter('status', type=str, required=False, description='Filter by application status'),
        OpenApiParameter('sort', type=str, required=False, description='Sort field e.g. -ai_match_score or -submitted_at')
    ],
    responses={200: ApplicationListSerializer(many=True)},
    tags=["Applications"]
)
class JobApplicationsView(generics.ListAPIView):
    """List applications for a specific job (employer only)"""
    
    serializer_class = ApplicationListSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get_queryset(self):
        job_id = self.kwargs['job_id']
        job = get_object_or_404(Job, id=job_id, employer=self.request.user)
        
        queryset = Application.objects.filter(job=job)
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Sort by AI match score
        sort_by = self.request.query_params.get('sort', '-ai_match_score')
        if sort_by == 'match_score':
            queryset = queryset.order_by('-ai_match_score', '-submitted_at')
        else:
            queryset = queryset.order_by('-submitted_at')
        
        return queryset


@extend_schema(
    summary="Update application status (employer)",
    description="Patch endpoint to change an application's status. Requires status and optional comment/rejection_reason.",
    request=ApplicationStatusUpdateSerializer,
    responses={200: OpenApiResponse(description='Updated application + message')},
    tags=["Applications"]
)
class ApplicationStatusUpdateView(views.APIView):
    """Update application status (employer only)"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def patch(self, request, pk):
        application = get_object_or_404(
            Application,
            pk=pk,
            job__employer=request.user
        )
        
        serializer = ApplicationStatusUpdateSerializer(
            data=request.data,
            context={'application': application}
        )
        serializer.is_valid(raise_exception=True)
        
        old_status = application.status
        new_status = serializer.validated_data['status']
        comment = serializer.validated_data.get('comment', '')
        
        # Update application
        application.status = new_status
        if new_status == 'under_review' and not application.reviewed_at:
            application.reviewed_at = timezone.now()
        
        if new_status == 'rejected':
            application.rejection_reason = serializer.validated_data.get('rejection_reason', '')
        
        application.save()
        
        # Create status history
        ApplicationStatusHistory.objects.create(
            application=application,
            old_status=old_status,
            new_status=new_status,
            changed_by=request.user,
            comment=comment
        )
        
        return Response({
            'message': 'Status updated successfully',
            'application': ApplicationSerializer(application).data
        })


@extend_schema(
    summary="Add a note to an application",
    description="Employer adds a note to an application. Returns created note.",
    request=ApplicationNoteSerializer,
    responses={201: OpenApiResponse(description='Created note')},
    tags=["Applications"]
)
class ApplicationNoteCreateView(generics.CreateAPIView):
    """Add note to application (employer only)"""
    
    serializer_class = ApplicationNoteSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def perform_create(self, serializer):
        application_id = self.kwargs['application_id']
        application = get_object_or_404(
            Application,
            pk=application_id,
            job__employer=self.request.user
        )
        
        serializer.save(
            application=application,
            author=self.request.user
        )


@extend_schema(
    summary="List notes for an application",
    description="Return notes attached to an application. Access restricted to the candidate and the job employer.",
    responses={200: ApplicationNoteSerializer(many=True)},
    tags=["Applications"]
)
class ApplicationNotesView(generics.ListAPIView):
    """List notes for an application"""
    
    serializer_class = ApplicationNoteSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        application_id = self.kwargs['application_id']
        
        # Check access
        user = self.request.user
        application = get_object_or_404(Application, pk=application_id)
        
        if user.is_employer and application.job.employer != user:
            return ApplicationNote.objects.none()
        elif not user.is_employer and application.user != user:
            return ApplicationNote.objects.none()
        
        return ApplicationNote.objects.filter(application_id=application_id)


@extend_schema(
    summary="Shortlist top candidates",
    description="Return top candidates for a job by AI match score (top 10).",
    responses={200: OpenApiResponse(description="job info + top_candidates list")},
    tags=["Applications"]
)
class ShortlistCandidatesView(views.APIView):
    """Get top candidates by AI match score"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get(self, request, job_id):
        job = get_object_or_404(Job, id=job_id, employer=request.user)
        
        # Get top 10 applications by AI match score
        top_applications = Application.objects.filter(
            job=job,
            ai_match_score__isnull=False
        ).order_by('-ai_match_score')[:10]
        
        serializer = ApplicationListSerializer(top_applications, many=True)
        
        return Response({
            'job_id': str(job.id),
            'job_title': job.title,
            'top_candidates': serializer.data
        })


@extend_schema(
    summary="Bulk update application statuses",
    description="Update statuses for multiple applications. Requires application_ids and status in the request body.",
    request=OpenApiResponse(description='application_ids list + status'),
    responses={200: OpenApiResponse(description='count of updated applications')},
    tags=["Applications"]
)
class BulkStatusUpdateView(views.APIView):
    """Bulk update application statuses"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def post(self, request):
        application_ids = request.data.get('application_ids', [])
        new_status = request.data.get('status')
        comment = request.data.get('comment', '')
        
        if not application_ids or not new_status:
            return Response(
                {'error': 'application_ids and status are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Get applications
        applications = Application.objects.filter(
            id__in=application_ids,
            job__employer=request.user
        )
        
        updated_count = 0
        for application in applications:
            old_status = application.status
            application.status = new_status
            application.save()
            
            ApplicationStatusHistory.objects.create(
                application=application,
                old_status=old_status,
                new_status=new_status,
                changed_by=request.user,
                comment=comment
            )
            updated_count += 1
        
        return Response({
            'message': f'{updated_count} applications updated',
            'updated_count': updated_count
        })