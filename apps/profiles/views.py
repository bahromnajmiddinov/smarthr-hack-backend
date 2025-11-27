from rest_framework import generics, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.parsers import MultiPartParser, FormParser
from django.shortcuts import get_object_or_404
from django.db.models import Count, Q

from .models import Profile, CV, Certificate
from .serializers import (
    ProfileSerializer,
    ProfileUpdateSerializer,
    CVSerializer,
    CVUploadSerializer,
    CertificateSerializer,
    ProfileStatsSerializer,
    GenerateCVSerializer
)
from .tasks import analyze_profile_with_ai, extract_cv_data, generate_cv_pdf
from drf_spectacular.utils import extend_schema, OpenApiResponse


@extend_schema(
    summary="Get or update current user's profile",
    description="Retrieve or update the authenticated user's profile. PUT/PATCH uses ProfileUpdateSerializer.",
    request=ProfileUpdateSerializer,
    responses={200: ProfileSerializer},
    tags=["Profiles"]
)
class MyProfileView(generics.RetrieveUpdateAPIView):
    """Get and update current user's profile"""
    
    permission_classes = [IsAuthenticated]
    
    def get_serializer_class(self):
        if self.request.method == 'PUT' or self.request.method == 'PATCH':
            return ProfileUpdateSerializer
        return ProfileSerializer
    
    def get_object(self):
        profile, created = Profile.objects.get_or_create(user=self.request.user)
        return profile
    
    def perform_update(self, serializer):
        profile = serializer.save()
        # Trigger AI analysis after update
        analyze_profile_with_ai.delay(profile.id)


@extend_schema(
    summary="Get public profile",
    description="Retrieve a public profile by user ID.",
    responses={200: ProfileSerializer},
    tags=["Profiles"]
)
class ProfileDetailView(generics.RetrieveAPIView):
    """View public profile by user ID"""
    
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    lookup_field = 'user_id'


@extend_schema(
    summary="List CVs for current user",
    description="Return all uploaded CV documents related to the authenticated user.",
    responses={200: CVSerializer(many=True)},
    tags=["Profiles"]
)
class CVListView(generics.ListAPIView):
    """List all CVs for current user"""
    
    serializer_class = CVSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        profile = get_object_or_404(Profile, user=self.request.user)
        return CV.objects.filter(profile=profile)


@extend_schema(
    summary="Upload CV document",
    description="Upload a new CV file (multipart). Returns created CV metadata.",
    request=CVUploadSerializer,
    responses={201: CVSerializer},
    tags=["Profiles"]
)
class CVUploadView(views.APIView):
    """Upload CV document"""
    
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]
    
    def post(self, request):
        serializer = CVUploadSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        file = serializer.validated_data['file']
        profile = get_object_or_404(Profile, user=request.user)
        
        # Create CV record
        cv = CV.objects.create(
            profile=profile,
            file=file,
            original_filename=file.name,
            file_type=file.content_type,
            file_size=file.size
        )
        
        # Trigger async CV extraction
        extract_cv_data.delay(cv.id)
        
        return Response(
            CVSerializer(cv).data,
            status=status.HTTP_201_CREATED
        )


@extend_schema(
    summary="Delete a CV",
    description="Delete a CV owned by the authenticated user.",
    responses={204: OpenApiResponse(description='Deleted')},
    tags=["Profiles"]
)
class CVDeleteView(generics.DestroyAPIView):
    """Delete CV"""
    
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        profile = get_object_or_404(Profile, user=self.request.user)
        return CV.objects.filter(profile=profile)


@extend_schema(
    summary="Generate CV (AI)",
    description="Start an async task to generate a CV PDF from profile data. Returns a task id.",
    request=GenerateCVSerializer,
    responses={202: OpenApiResponse(description='Job queued')},
    tags=["Profiles"]
)
class GenerateCVView(views.APIView):
    """AI-generate CV from profile data"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        serializer = GenerateCVSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        profile = get_object_or_404(Profile, user=request.user)
        
        # Trigger async CV generation
        task = generate_cv_pdf.delay(
            profile.id,
            serializer.validated_data['template'],
            serializer.validated_data['include_photo'],
            serializer.validated_data['sections']
        )
        
        return Response({
            'message': 'CV generation started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)


@extend_schema(
    summary="List and create certificates",
    description="List and create certificates for the authenticated user.",
    request=CertificateSerializer,
    responses={200: CertificateSerializer(many=True), 201: OpenApiResponse(description='Created')},
    tags=["Profiles"]
)
class CertificateListCreateView(generics.ListCreateAPIView):
    """List and create certificates"""
    
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        profile = get_object_or_404(Profile, user=self.request.user)
        return Certificate.objects.filter(profile=profile)
    
    def perform_create(self, serializer):
        profile = get_object_or_404(Profile, user=self.request.user)
        serializer.save(profile=profile)


@extend_schema(
    summary="Retrieve / update / delete certificate",
    description="Manage an individual certificate owned by the authenticated user.",
    request=CertificateSerializer,
    responses={200: CertificateSerializer, 204: OpenApiResponse(description='Deleted')},
    tags=["Profiles"]
)
class CertificateDetailView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update, or delete certificate"""
    
    serializer_class = CertificateSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        profile = get_object_or_404(Profile, user=self.request.user)
        return Certificate.objects.filter(profile=profile)


@extend_schema(
    summary="Profile statistics",
    description="Get aggregate stats for the current user's profile and activity.",
    responses={200: ProfileStatsSerializer},
    tags=["Profiles"]
)
class ProfileStatsView(views.APIView):
    """Get profile statistics"""
    
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        
        from apps.applications.models import Application
        from apps.interviews.models import Interview
        
        # Calculate stats
        applications = Application.objects.filter(user=request.user)
        interviews = Interview.objects.filter(application__user=request.user)
        
        stats = {
            'total_applications': applications.count(),
            'active_applications': applications.filter(
                status__in=['submitted', 'under_review', 'shortlisted']
            ).count(),
            'interviews_completed': interviews.filter(status='completed').count(),
            'interviews_scheduled': interviews.filter(status='scheduled').count(),
            'profile_views': 0,  # TODO: Implement view tracking
            'profile_completeness': self._calculate_completeness(profile)
        }
        
        serializer = ProfileStatsSerializer(stats)
        return Response(serializer.data)
    
    def _calculate_completeness(self, profile):
        """Calculate profile completeness percentage"""
        fields = [
            profile.bio,
            profile.avatar,
            profile.date_of_birth,
            profile.location,
            profile.skills,
            profile.education,
            profile.experience,
        ]
        
        filled = sum(1 for field in fields if field)
        return (filled / len(fields)) * 100


@extend_schema(
    summary="Analyze profile (AI)",
    description="Trigger asynchronous AI analysis for the authenticated user's profile.",
    responses={202: OpenApiResponse(description='Analysis started')},
    tags=["Profiles"]
)
class AnalyzeProfileView(views.APIView):
    """Trigger AI analysis of profile"""
    
    permission_classes = [IsAuthenticated]
    
    def post(self, request):
        profile = get_object_or_404(Profile, user=request.user)
        
        # Trigger async analysis
        task = analyze_profile_with_ai.delay(profile.id)
        
        return Response({
            'message': 'Profile analysis started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)