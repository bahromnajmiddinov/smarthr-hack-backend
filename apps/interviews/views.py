from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg, Q

from .models import Interview, InterviewQuestion, InterviewFeedback
from .serializers import (
    InterviewSerializer,
    InterviewCreateSerializer,
    InterviewUpdateSerializer,
    InterviewListSerializer,
    VideoUploadSerializer,
    InterviewQuestionSerializer,
    InterviewFeedbackSerializer,
    InterviewStatsSerializer
)
from apps.applications.models import Application
from apps.common.permissions import IsEmployer
from .tasks import analyze_interview_video
from drf_spectacular.utils import extend_schema, OpenApiResponse, OpenApiParameter


@extend_schema(
    summary="List interviews for current user",
    description="Returns interviews for the authenticated user; employers see interviews for their jobs, candidates see their own.",
    parameters=[OpenApiParameter('status', required=False, type=str, description='Filter by interview status'), OpenApiParameter('time', required=False, type=str, description='Filter by upcoming/past')],
    responses={200: InterviewListSerializer(many=True)},
    tags=["Interviews"]
)
class InterviewListView(generics.ListAPIView):
    """List all interviews for current user"""
    
    serializer_class = InterviewListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_employer:
            # Employers see interviews for their jobs
            queryset = Interview.objects.filter(
                application__job__employer=user
            )
        else:
            # Candidates see their own interviews
            queryset = Interview.objects.filter(
                application__user=user
            )
        
        # Filter by status
        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        # Filter by upcoming/past
        time_filter = self.request.query_params.get('time')
        if time_filter == 'upcoming':
            queryset = queryset.filter(
                scheduled_at__gte=timezone.now(),
                status='scheduled'
            )
        elif time_filter == 'past':
            queryset = queryset.filter(
                Q(scheduled_at__lt=timezone.now()) |
                Q(status='completed')
            )
        
        return queryset.order_by('-scheduled_at')


@extend_schema(
    summary="Schedule an interview",
    description="Employer schedules an interview for a given application id and meeting details.",
    request=InterviewCreateSerializer,
    responses={201: OpenApiResponse(description='Interview created')},
    tags=["Interviews"]
)
class InterviewCreateView(generics.CreateAPIView):
    """Schedule an interview (employer only)"""
    
    serializer_class = InterviewCreateSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def perform_create(self, serializer):
        application_id = serializer.validated_data.pop('application_id')
        application = get_object_or_404(Application, id=application_id)
        
        interview = serializer.save(
            application=application,
            interviewer=self.request.user
        )
        
        # Update application status
        if application.status != 'interview_scheduled':
            application.status = 'interview_scheduled'
            application.save()
        
        return interview


@extend_schema(
    summary="Interview details",
    description="Retrieve a single interview entry with all related metadata and AI scores.",
    responses={200: InterviewSerializer},
    tags=["Interviews"]
)
class InterviewDetailView(generics.RetrieveAPIView):
    """Get interview details"""
    
    serializer_class = InterviewSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        if user.is_employer:
            return Interview.objects.filter(
                application__job__employer=user
            )
        else:
            return Interview.objects.filter(
                application__user=user
            )


@extend_schema(
    summary="Update interview",
    description="Employer can update interview fields such as scheduled_at/status and add feedback/rating.",
    request=InterviewUpdateSerializer,
    responses={200: OpenApiResponse(description='Updated interview')},
    tags=["Interviews"]
)
class InterviewUpdateView(generics.UpdateAPIView):
    """Update interview details"""
    
    serializer_class = InterviewUpdateSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get_queryset(self):
        return Interview.objects.filter(
            application__job__employer=self.request.user
        )
    
    def perform_update(self, serializer):
        interview = serializer.save()
        
        # Set completed_at when status changes to completed
        if interview.status == 'completed' and not interview.completed_at:
            interview.completed_at = timezone.now()
            interview.save()
            
            # Update application status
            if interview.application.status == 'interview_scheduled':
                interview.application.status = 'interviewed'
                interview.application.save()


@extend_schema(
    summary="Cancel an interview",
    description="Cancel an interview if it hasn't already been completed or cancelled.",
    responses={200: OpenApiResponse(description='Success message'), 400: OpenApiResponse(description='Cannot cancel')},
    tags=["Interviews"]
)
class InterviewCancelView(views.APIView):
    """Cancel an interview"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request, pk):
        user = request.user
        
        if user.is_employer:
            interview = get_object_or_404(
                Interview,
                pk=pk,
                application__job__employer=user
            )
        else:
            interview = get_object_or_404(
                Interview,
                pk=pk,
                application__user=user
            )
        
        if interview.status in ['completed', 'cancelled']:
            return Response(
                {'error': 'Cannot cancel this interview'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.status = 'cancelled'
        interview.save()
        
        return Response({
            'message': 'Interview cancelled successfully'
        })


@extend_schema(
    summary="Reschedule an interview",
    description="Modify the scheduled_at time for an interview (employer only).",
    request=OpenApiResponse(description='scheduled_at required'),
    responses={200: OpenApiResponse(description='Interview updated')},
    tags=["Interviews"]
)
class InterviewRescheduleView(views.APIView):
    """Reschedule an interview"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def post(self, request, pk):
        interview = get_object_or_404(
            Interview,
            pk=pk,
            application__job__employer=request.user
        )
        
        new_time = request.data.get('scheduled_at')
        if not new_time:
            return Response(
                {'error': 'scheduled_at is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        interview.scheduled_at = new_time
        interview.status = 'rescheduled'
        interview.save()
        
        return Response({
            'message': 'Interview rescheduled successfully',
            'interview': InterviewSerializer(interview).data
        })


@extend_schema(
    summary="Upload interview video",
    description="Upload a recorded interview video (multipart file upload). Triggers async AI analysis.",
    request=VideoUploadSerializer,
    responses={201: OpenApiResponse(description='Upload accepted')},
    tags=["Interviews"]
)
class VideoUploadView(views.APIView):
    """Upload interview video"""
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request, pk):
        # Check access
        user = request.user
        if user.is_employer:
            interview = get_object_or_404(
                Interview,
                pk=pk,
                application__job__employer=user
            )
        else:
            interview = get_object_or_404(
                Interview,
                pk=pk,
                application__user=user
            )
        
        serializer = VideoUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        # Save video file
        interview.video_file = serializer.validated_data['video_file']
        interview.save()
        
        # Trigger AI analysis
        analyze_interview_video.delay(interview.id)
        
        return Response({
            'message': 'Video uploaded successfully',
            'video_url': interview.video_file.url if interview.video_file else None
        })


@extend_schema(
    summary="List/create interview questions",
    description="List and create interview questions for an interview. Employers may add questions.",
    request=InterviewQuestionSerializer,
    responses={200: InterviewQuestionSerializer(many=True), 201: OpenApiResponse(description='Question created')},
    tags=["Interviews"]
)
class InterviewQuestionsView(generics.ListCreateAPIView):
    """List and create interview questions"""
    
    serializer_class = InterviewQuestionSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        interview_id = self.kwargs['interview_id']
        
        # Check access
        user = self.request.user
        interview = get_object_or_404(Interview, pk=interview_id)
        
        if user.is_employer and interview.application.job.employer != user:
            return InterviewQuestion.objects.none()
        elif not user.is_employer and interview.application.user != user:
            return InterviewQuestion.objects.none()
        
        return InterviewQuestion.objects.filter(interview_id=interview_id)
    
    def perform_create(self, serializer):
        interview_id = self.kwargs['interview_id']
        interview = get_object_or_404(
            Interview,
            pk=interview_id,
            application__job__employer=self.request.user
        )
        
        serializer.save(interview=interview)


@extend_schema(
    summary="Submit candidate feedback",
    description="A candidate can submit feedback and rating for a completed interview.",
    request=InterviewFeedbackSerializer,
    responses={201: OpenApiResponse(description='Feedback recorded')},
    tags=["Interviews"]
)
class InterviewFeedbackView(generics.CreateAPIView):
    """Submit candidate feedback about interview"""
    
    serializer_class = InterviewFeedbackSerializer
    permission_classes = [IsAuthenticated]
    
    def perform_create(self, serializer):
        interview_id = self.kwargs['interview_id']
        interview = get_object_or_404(
            Interview,
            pk=interview_id,
            application__user=self.request.user
        )
        
        serializer.save(interview=interview)


@extend_schema(
    summary="Interview stats (employer)",
    description="Return aggregated interview statistics for the employer's jobs.",
    responses={200: InterviewStatsSerializer},
    tags=["Interviews"]
)
class InterviewStatsView(views.APIView):
    """Get interview statistics"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get(self, request):
        interviews = Interview.objects.filter(
            application__job__employer=request.user
        )
        
        stats = {
            'total_interviews': interviews.count(),
            'scheduled_interviews': interviews.filter(status='scheduled').count(),
            'completed_interviews': interviews.filter(status='completed').count(),
            'avg_rating': interviews.filter(
                interviewer_rating__isnull=False
            ).aggregate(avg=Avg('interviewer_rating'))['avg'] or 0,
            'avg_ai_score': interviews.filter(
                ai_score__isnull=False
            ).aggregate(avg=Avg('ai_score'))['avg'] or 0,
        }
        
        serializer = InterviewStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema(
    summary="Upcoming interviews",
    description="Get a short list of upcoming interviews for the user (first 5).",
    responses={200: InterviewListSerializer(many=True)},
    tags=["Interviews"]
)
class UpcomingInterviewsView(generics.ListAPIView):
    """Get upcoming interviews"""
    
    serializer_class = InterviewListSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        user = self.request.user
        
        base_query = Q(
            scheduled_at__gte=timezone.now(),
            status='scheduled'
        )
        
        if user.is_employer:
            return Interview.objects.filter(
                base_query,
                application__job__employer=user
            ).order_by('scheduled_at')[:5]
        else:
            return Interview.objects.filter(
                base_query,
                application__user=user
            ).order_by('scheduled_at')[:5]