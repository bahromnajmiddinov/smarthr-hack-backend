from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Avg, Count
from django.shortcuts import get_object_or_404
from django.utils import timezone

from .models import Job, JobView
from .serializers import (
    JobSerializer,
    JobCreateSerializer,
    JobUpdateSerializer,
    JobListSerializer,
    JobStatsSerializer,
    JobSearchSerializer
)
from apps.common.permissions import IsEmployer
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


@extend_schema(
    summary="Search and list active jobs",
    description="Search open jobs with optional filters and ordering.",
    parameters=[
        OpenApiParameter('q', type=str, description='Full text search across job title/description'),
        OpenApiParameter('location', type=str, description='Filter by location'),
        OpenApiParameter('is_remote', type=bool, description='Filter remote jobs'),
        OpenApiParameter('job_type', type=str, description='Filter by job type'),
        OpenApiParameter('salary_min', type=float, description='Minimum salary filter'),
        OpenApiParameter('skills', type=str, description='Comma separated required skills'),
        OpenApiParameter('experience_years', type=int, description='Experience years filter'),
        OpenApiParameter('ordering', type=str, description='Ordering key')
    ],
    responses={200: JobListSerializer(many=True)},
    tags=["Jobs"]
)
class JobListView(generics.ListAPIView):
    """List all active jobs with search and filters"""
    
    serializer_class = JobListSerializer
    permission_classes = [AllowAny]
    
    def get_queryset(self):
        queryset = Job.objects.filter(status='open')
        
        # Search query
        q = self.request.query_params.get('q')
        if q:
            queryset = queryset.filter(
                Q(title__icontains=q) |
                Q(description__icontains=q) |
                Q(required_skills__contains=[q])
            )
        
        # Location filter
        location = self.request.query_params.get('location')
        if location:
            queryset = queryset.filter(location__icontains=location)
        
        # Remote filter
        is_remote = self.request.query_params.get('is_remote')
        if is_remote:
            queryset = queryset.filter(is_remote=is_remote.lower() == 'true')
        
        # Job type filter
        job_type = self.request.query_params.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        # Salary filter
        salary_min = self.request.query_params.get('salary_min')
        if salary_min:
            queryset = queryset.filter(salary_min__gte=salary_min)
        
        # Skills filter
        skills = self.request.query_params.get('skills')
        if skills:
            skills_list = skills.split(',')
            for skill in skills_list:
                queryset = queryset.filter(required_skills__contains=[skill.strip()])
        
        # Experience filter
        experience = self.request.query_params.get('experience_years')
        if experience:
            queryset = queryset.filter(
                experience_years_min__lte=experience,
                experience_years_max__gte=experience
            )
        
        # Ordering
        ordering = self.request.query_params.get('ordering', '-created_at')
        queryset = queryset.order_by(ordering)
        
        return queryset


@extend_schema(
    summary="Create a new job posting",
    description="Employer creates a new job posting; accepts full job details.",
    request=JobCreateSerializer,
    responses={201: JobSerializer},
    tags=["Jobs"]
)
class JobCreateView(generics.CreateAPIView):
    """Create new job posting (employers only)"""
    
    serializer_class = JobCreateSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def perform_create(self, serializer):
        job = serializer.save(employer=self.request.user)
        # Auto-publish if not draft
        if job.status == 'open':
            job.published_at = timezone.now()
            job.save()


@extend_schema(
    summary="Get job details",
    description="Retrieve a job posting. Authenticated requests may record a view and create JobView objects.",
    responses={200: JobSerializer},
    tags=["Jobs"]
)
class JobDetailView(generics.RetrieveAPIView):
    """Get job details"""
    
    queryset = Job.objects.all()
    serializer_class = JobSerializer
    permission_classes = [AllowAny]
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        
        # Track view
        if request.user.is_authenticated:
            JobView.objects.create(
                job=instance,
                user=request.user,
                ip_address=self.get_client_ip(request)
            )
        
        # Increment view count
        instance.views_count += 1
        instance.save(update_fields=['views_count'])
        
        serializer = self.get_serializer(instance)
        return Response(serializer.data)
    
    def get_client_ip(self, request):
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip


@extend_schema(
    summary="Update job posting",
    description="Employer updates a job posting. If status becomes open, published_at may be set.",
    request=JobUpdateSerializer,
    responses={200: JobSerializer},
    tags=["Jobs"]
)
class JobUpdateView(generics.UpdateAPIView):
    """Update job posting"""
    
    serializer_class = JobUpdateSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get_queryset(self):
        return Job.objects.filter(employer=self.request.user)
    
    def perform_update(self, serializer):
        job = serializer.save()
        # Set published date when status changes to open
        if job.status == 'open' and not job.published_at:
            job.published_at = timezone.now()
            job.save()


@extend_schema(
    summary="Delete job posting",
    description="Remove a job posting created by the employer.",
    responses={204: OpenApiResponse(description='Deleted')},
    tags=["Jobs"]
)
class JobDeleteView(generics.DestroyAPIView):
    """Delete job posting"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get_queryset(self):
        return Job.objects.filter(employer=self.request.user)


@extend_schema(
    summary="List my jobs (employer)",
    description="List jobs created by the authenticated employer.",
    responses={200: JobListSerializer(many=True)},
    tags=["Jobs"]
)
class MyJobsView(generics.ListAPIView):
    """List jobs posted by current employer"""
    
    serializer_class = JobListSerializer
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get_queryset(self):
        return Job.objects.filter(employer=self.request.user).order_by('-created_at')


@extend_schema(
    summary="Job statistics for employer",
    description="Returns aggregate metrics across the employer's jobs (views, applications, etc).",
    responses={200: JobStatsSerializer},
    tags=["Jobs"]
)
class JobStatsView(views.APIView):
    """Get statistics for employer's jobs"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def get(self, request):
        jobs = Job.objects.filter(employer=request.user)
        
        stats = {
            'total_jobs': jobs.count(),
            'active_jobs': jobs.filter(status='open').count(),
            'total_applications': sum(job.applications_count for job in jobs),
            'avg_applications_per_job': jobs.aggregate(
                avg=Avg('applications_count')
            )['avg'] or 0,
            'total_views': sum(job.views_count for job in jobs),
        }
        
        serializer = JobStatsSerializer(stats)
        return Response(serializer.data)


@extend_schema(
    summary="AI job recommendations for candidate",
    description="Return personalized job recommendations using AI service for the authenticated candidate.",
    responses={200: OpenApiResponse(description='List of recommended jobs')},
    tags=["Jobs"]
)
class JobRecommendationsView(views.APIView):
    """Get AI-powered job recommendations for candidate"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        from apps.profiles.models import Profile
        from apps.common.ai_service import AIService
        
        try:
            profile = Profile.objects.get(user=request.user)
        except Profile.DoesNotExist:
            return Response(
                {'error': 'Profile not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # Get active jobs
        jobs = Job.objects.filter(status='open')
        
        # Get AI recommendations
        ai_service = AIService()
        recommendations = ai_service.recommend_jobs(profile, jobs)
        
        return Response({
            'recommendations': recommendations
        })


@extend_schema(
    summary="Publish a draft job",
    description="Change a draft job's status to open and set published_at.",
    responses={200: JobSerializer},
    tags=["Jobs"]
)
class JobPublishView(views.APIView):
    """Publish a draft job"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, employer=request.user)
        
        if job.status != 'draft':
            return Response(
                {'error': 'Job is not in draft status'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        job.status = 'open'
        job.published_at = timezone.now()
        job.save()
        
        return Response({
            'message': 'Job published successfully',
            'job': JobSerializer(job).data
        })


@extend_schema(
    summary="Close an active job",
    description="Close an open job posting.",
    responses={200: OpenApiResponse(description='Confirmation')},
    tags=["Jobs"]
)
class JobCloseView(views.APIView):
    """Close an active job"""
    
    permission_classes = [IsAuthenticated, IsEmployer]
    
    def post(self, request, pk):
        job = get_object_or_404(Job, pk=pk, employer=request.user)
        
        job.status = 'closed'
        job.save()
        
        return Response({
            'message': 'Job closed successfully'
        })