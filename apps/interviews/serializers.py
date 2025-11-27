from rest_framework import serializers
from .models import Interview, InterviewQuestion, InterviewFeedback
from apps.applications.serializers import ApplicationListSerializer
from apps.accounts.serializers import UserSerializer


class InterviewSerializer(serializers.ModelSerializer):
    """Serializer for Interview model"""
    
    application = ApplicationListSerializer(read_only=True)
    interviewer = UserSerializer(read_only=True)
    candidate_name = serializers.CharField(
        source='application.user.full_name',
        read_only=True
    )
    job_title = serializers.CharField(
        source='application.job.title',
        read_only=True
    )
    
    class Meta:
        model = Interview
        fields = [
            'id', 'application', 'interview_type', 'status',
            'scheduled_at', 'duration_minutes', 'location', 'meeting_url',
            'interviewer', 'candidate_name', 'job_title',
            'video_url', 'video_file', 'ai_review', 'ai_score', 'ai_analyzed_at',
            'interviewer_feedback', 'interviewer_rating', 'notes',
            'created_at', 'updated_at', 'completed_at'
        ]
        read_only_fields = [
            'id', 'application', 'ai_review', 'ai_score', 'ai_analyzed_at',
            'created_at', 'updated_at', 'completed_at'
        ]
        extra_kwargs = {
            'interview_type': {'help_text': 'Type of interview (e.g., phone, video, on-site)'},
            'status': {'help_text': 'Interview status string'},
            'scheduled_at': {'help_text': 'ISO8601 datetime when interview is scheduled'},
            'duration_minutes': {'help_text': 'Planned duration in minutes'}
        }


class InterviewCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating/scheduling interviews"""
    
    application_id = serializers.UUIDField(write_only=True, help_text='Application UUID to create the interview for')
    
    class Meta:
        model = Interview
        fields = [
            'application_id', 'interview_type', 'scheduled_at',
            'duration_minutes', 'location', 'meeting_url', 'notes'
        ]
    
    def validate_application_id(self, value):
        """Validate application exists and belongs to employer"""
        from apps.applications.models import Application
        
        try:
            application = Application.objects.get(id=value)
        except Application.DoesNotExist:
            raise serializers.ValidationError("Application not found")
        
        # Check if employer owns this job
        request = self.context.get('request')
        if request and application.job.employer != request.user:
            raise serializers.ValidationError("You don't have permission for this application")
        
        return value


class InterviewUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating interviews"""
    
    class Meta:
        model = Interview
        fields = [
            'interview_type', 'status', 'scheduled_at', 'duration_minutes',
            'location', 'meeting_url', 'interviewer_feedback',
            'interviewer_rating', 'notes'
        ]
        extra_kwargs = {
            'status': {'help_text': 'New status (rescheduled/completed/cancelled etc)'},
        }


class InterviewListSerializer(serializers.ModelSerializer):
    """Minimal serializer for interview listings"""
    
    candidate_name = serializers.CharField(source='application.user.full_name', read_only=True)
    job_title = serializers.CharField(source='application.job.title', read_only=True)
    company_name = serializers.CharField(source='application.job.employer.full_name', read_only=True)
    
    class Meta:
        model = Interview
        fields = [
            'id', 'interview_type', 'status', 'scheduled_at',
            'candidate_name', 'job_title', 'company_name',
            'ai_score', 'interviewer_rating'
        ]


class VideoUploadSerializer(serializers.Serializer):
    """Serializer for video upload"""
    
    video_file = serializers.FileField(required=True, help_text='Video file (.mp4/.mov/.webm) max 100MB')
    
    def validate_video_file(self, value):
        """Validate video file"""
        # Check file size (max 100MB)
        if value.size > 100 * 1024 * 1024:
            raise serializers.ValidationError("Video size cannot exceed 100MB")
        
        # Check file extension
        allowed_extensions = ['.mp4', '.avi', '.mov', '.webm']
        ext = value.name.lower().split('.')[-1]
        if f'.{ext}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        return value


class InterviewQuestionSerializer(serializers.ModelSerializer):
    """Serializer for interview questions"""
    
    class Meta:
        model = InterviewQuestion
        fields = ['id', 'interview', 'question_text', 'answer_text', 'ai_score', 'order']
        read_only_fields = ['id', 'interview', 'ai_score']
        extra_kwargs = {
            'question_text': {'help_text': 'Question prompt text'},
            'answer_text': {'help_text': 'Candidate-provided answer text'},
            'order': {'help_text': 'Ordering position for question list'}
        }


class InterviewFeedbackSerializer(serializers.ModelSerializer):
    """Serializer for candidate feedback"""
    
    class Meta:
        model = InterviewFeedback
        fields = ['id', 'interview', 'rating', 'comments', 'created_at']
        read_only_fields = ['id', 'interview', 'created_at']
    
    def validate_rating(self, value):
        if value < 1 or value > 5:
            raise serializers.ValidationError("Rating must be between 1 and 5")
        return value


class InterviewStatsSerializer(serializers.Serializer):
    """Serializer for interview statistics"""
    
    total_interviews = serializers.IntegerField()
    scheduled_interviews = serializers.IntegerField()
    completed_interviews = serializers.IntegerField()
    avg_rating = serializers.FloatField()
    avg_ai_score = serializers.FloatField()