from rest_framework import serializers
from .models import Job, JobView
from apps.accounts.serializers import UserSerializer


class JobSerializer(serializers.ModelSerializer):
    """Serializer for Job model"""
    
    employer = UserSerializer(read_only=True)
    is_applied = serializers.SerializerMethodField()
    
    class Meta:
        model = Job
        fields = [
            'id', 'employer', 'title', 'description', 'requirements',
            'responsibilities', 'location', 'is_remote', 'job_type',
            'salary_min', 'salary_max', 'salary_currency',
            'required_skills', 'preferred_skills',
            'experience_years_min', 'experience_years_max',
            'status', 'deadline', 'views_count', 'applications_count',
            'is_applied', 'created_at', 'updated_at', 'published_at'
        ]
        read_only_fields = [
            'id', 'employer', 'views_count', 'applications_count',
            'created_at', 'updated_at', 'published_at'
        ]
        extra_kwargs = {
            'title': {'help_text': 'Short, descriptive job title'},
            'description': {'help_text': 'Full job description and responsibilities'},
            'location': {'help_text': 'Human readable location or address'},
            'job_type': {'help_text': 'Full-time, part-time, contract, etc.'},
            'salary_min': {'help_text': 'Minimum salary for the role'},
            'salary_max': {'help_text': 'Maximum salary for the role'},
            'required_skills': {'help_text': 'List of required skills for the job'}
        }
    
    def get_is_applied(self, obj):
        """Check if current user has applied"""
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            from apps.applications.models import Application
            return Application.objects.filter(
                job=obj,
                user=request.user
            ).exists()
        return False
    
    def validate(self, attrs):
        """Validate job data"""
        # Validate salary range
        salary_min = attrs.get('salary_min')
        salary_max = attrs.get('salary_max')
        
        if salary_min and salary_max and salary_min > salary_max:
            raise serializers.ValidationError({
                'salary_max': 'Maximum salary must be greater than minimum salary'
            })
        
        # Validate experience years
        exp_min = attrs.get('experience_years_min', 0)
        exp_max = attrs.get('experience_years_max')
        
        if exp_max and exp_min > exp_max:
            raise serializers.ValidationError({
                'experience_years_max': 'Maximum experience must be greater than minimum'
            })
        
        return attrs


class JobCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating jobs"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'responsibilities',
            'location', 'is_remote', 'job_type',
            'salary_min', 'salary_max', 'salary_currency',
            'required_skills', 'preferred_skills',
            'experience_years_min', 'experience_years_max',
            'deadline'
        ]
        extra_kwargs = {
            'title': {'help_text': 'Short title for the job'},
            'description': {'help_text': 'Detailed job description'},
            'deadline': {'help_text': 'Application deadline in ISO format'}
        }


class JobUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating jobs"""
    
    class Meta:
        model = Job
        fields = [
            'title', 'description', 'requirements', 'responsibilities',
            'location', 'is_remote', 'job_type',
            'salary_min', 'salary_max', 'salary_currency',
            'required_skills', 'preferred_skills',
            'experience_years_min', 'experience_years_max',
            'status', 'deadline'
        ]
        extra_kwargs = {
            'status': {'help_text': "Job lifecycle state: 'draft', 'open', 'closed', 'filled'"}
        }


class JobListSerializer(serializers.ModelSerializer):
    """Minimal serializer for job listings"""
    
    employer_name = serializers.CharField(source='employer.full_name', read_only=True)
    
    class Meta:
        model = Job
        fields = [
            'id', 'title', 'employer_name', 'location', 'is_remote',
            'job_type', 'salary_min', 'salary_max', 'salary_currency',
            'required_skills', 'experience_years_min', 'status',
            'views_count', 'applications_count', 'created_at', 'deadline'
        ]
        extra_kwargs = {
            'views_count': {'help_text': 'Number of times this listing has been viewed'},
            'applications_count': {'help_text': 'Number of applications received'}
        }


class JobStatsSerializer(serializers.Serializer):
    """Serializer for job statistics"""
    
    total_jobs = serializers.IntegerField()
    active_jobs = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    avg_applications_per_job = serializers.FloatField()
    total_views = serializers.IntegerField()


class JobSearchSerializer(serializers.Serializer):
    """Serializer for job search parameters"""
    
    q = serializers.CharField(required=False, help_text='Search query')
    location = serializers.CharField(required=False)
    job_type = serializers.CharField(required=False)
    is_remote = serializers.BooleanField(required=False)
    salary_min = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    salary_max = serializers.DecimalField(max_digits=10, decimal_places=2, required=False)
    skills = serializers.ListField(
        child=serializers.CharField(),
        required=False
    )
    experience_years = serializers.IntegerField(required=False)
    ordering = serializers.ChoiceField(
        choices=['-created_at', 'created_at', '-salary_max', 'salary_max'],
        default='-created_at',
        required=False
    )