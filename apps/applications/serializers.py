from rest_framework import serializers
from .models import Application, ApplicationNote, ApplicationStatusHistory
from apps.accounts.serializers import UserSerializer
from apps.jobs.serializers import JobListSerializer


class ApplicationSerializer(serializers.ModelSerializer):
    """Serializer for Application model"""
    
    user = UserSerializer(read_only=True)
    job = JobListSerializer(read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'job', 'user', 'cover_letter', 'cv_file',
            'status', 'ai_match_score', 'ai_analysis', 'ai_analyzed_at',
            'employer_notes', 'rejection_reason',
            'submitted_at', 'reviewed_at', 'updated_at'
        ]
        read_only_fields = [
            'id', 'user', 'job', 'ai_match_score', 'ai_analysis',
            'ai_analyzed_at', 'submitted_at', 'reviewed_at', 'updated_at'
        ]
        extra_kwargs = {
            'cover_letter': {'help_text': 'Optional cover letter text provided by candidate'},
            'cv_file': {'help_text': 'Optional uploaded CV file'},
            'status': {'help_text': 'Application status string (see Application.STATUS_CHOICES)'},
        }


class ApplicationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating applications"""
    
    job_id = serializers.UUIDField(write_only=True, help_text='UUID of the job to apply for')
    
    class Meta:
        model = Application
        fields = ['job_id', 'cover_letter', 'cv_file']
    
    def validate_job_id(self, value):
        """Validate job exists and is open"""
        from apps.jobs.models import Job
        
        try:
            job = Job.objects.get(id=value)
        except Job.DoesNotExist:
            raise serializers.ValidationError("Job not found")
        
        if job.status != 'open':
            raise serializers.ValidationError("Job is not open for applications")
        
        return value
    
    def validate(self, attrs):
        """Check if user already applied"""
        user = self.context['request'].user
        job_id = attrs['job_id']
        
        if Application.objects.filter(user=user, job_id=job_id).exists():
            raise serializers.ValidationError("You have already applied to this job")
        
        return attrs


class ApplicationListSerializer(serializers.ModelSerializer):
    """Minimal serializer for application listings"""
    
    job_title = serializers.CharField(source='job.title', read_only=True)
    job_id = serializers.UUIDField(source='job.id', read_only=True)
    company_name = serializers.CharField(source='job.employer.full_name', read_only=True)
    candidate_name = serializers.CharField(source='user.full_name', read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'job_id', 'job_title', 'company_name', 'candidate_name',
            'status', 'ai_match_score', 'submitted_at'
        ]
        extra_kwargs = {
            'ai_match_score': {'help_text': 'AI-derived match score (0.0 - 1.0)'}
        }


class ApplicationStatusUpdateSerializer(serializers.Serializer):
    """Serializer for updating application status"""
    
    status = serializers.ChoiceField(choices=Application.STATUS_CHOICES, help_text='New status to transition to')
    comment = serializers.CharField(required=False, allow_blank=True, help_text='Optional internal/external comment')
    rejection_reason = serializers.CharField(required=False, allow_blank=True, help_text='Optional rejection reason shown to candidate')
    
    def validate_status(self, value):
        """Validate status transition"""
        application = self.context.get('application')
        
        if not application:
            return value
        
        # Define valid transitions
        valid_transitions = {
            'submitted': ['under_review', 'rejected'],
            'under_review': ['shortlisted', 'rejected'],
            'shortlisted': ['interview_scheduled', 'rejected'],
            'interview_scheduled': ['interviewed', 'no_show', 'rejected'],
            'interviewed': ['offer_sent', 'rejected'],
            'offer_sent': ['accepted', 'rejected'],
        }
        
        current_status = application.status
        allowed = valid_transitions.get(current_status, [])
        
        if value not in allowed and value != current_status:
            raise serializers.ValidationError(
                f"Cannot transition from {current_status} to {value}"
            )
        
        return value


class ApplicationNoteSerializer(serializers.ModelSerializer):
    """Serializer for application notes"""
    
    author_name = serializers.CharField(source='author.full_name', read_only=True, help_text="Author's display name")
    
    class Meta:
        model = ApplicationNote
        fields = ['id', 'application', 'author', 'author_name', 'content', 'created_at']
        read_only_fields = ['id', 'application', 'author', 'author_name', 'created_at']


class ApplicationStatusHistorySerializer(serializers.ModelSerializer):
    """Serializer for status history"""
    
    changed_by_name = serializers.CharField(source='changed_by.full_name', read_only=True, help_text='Display name of the user who made the change')
    
    class Meta:
        model = ApplicationStatusHistory
        fields = [
            'id', 'old_status', 'new_status',
            'changed_by', 'changed_by_name', 'comment', 'changed_at'
        ]
        read_only_fields = ['id', 'changed_by_name', 'changed_at']


class ApplicationDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer with related data"""
    
    user = UserSerializer(read_only=True)
    job = JobListSerializer(read_only=True)
    notes = ApplicationNoteSerializer(many=True, read_only=True)
    status_history = ApplicationStatusHistorySerializer(many=True, read_only=True)
    
    class Meta:
        model = Application
        fields = [
            'id', 'job', 'user', 'cover_letter', 'cv_file',
            'status', 'ai_match_score', 'ai_analysis', 'ai_analyzed_at',
            'employer_notes', 'rejection_reason',
            'notes', 'status_history',
            'submitted_at', 'reviewed_at', 'updated_at'
        ]