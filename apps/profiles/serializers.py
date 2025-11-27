from rest_framework import serializers
from .models import Profile, CV, Certificate
from apps.accounts.serializers import UserSerializer


class ProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile"""
    
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'bio', 'avatar', 'date_of_birth', 'location',
            'skills', 'education', 'experience', 'certifications', 'languages',
            'ai_score', 'ai_analyzed_at', 'linkedin_url', 'github_url',
            'portfolio_url', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'user', 'ai_score', 'ai_analyzed_at', 'created_at', 'updated_at']
        extra_kwargs = {
            'bio': {'help_text': 'Short biography or summary'},
            'avatar': {'help_text': 'URL or file reference to avatar image'},
            'skills': {'help_text': 'List of skill strings'},
            'education': {'help_text': 'Structured education objects (institution/degree/field)'},
            'experience': {'help_text': 'Structured experience entries'},
            'linkedin_url': {'help_text': 'Optional LinkedIn profile URL'},
            'github_url': {'help_text': 'Optional GitHub profile URL'}
        }
    
    def validate_skills(self, value):
        """Validate skills format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Skills must be a list")
        return value
    
    def validate_education(self, value):
        """Validate education format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Education must be a list")
        
        for edu in value:
            required_fields = ['institution', 'degree', 'field']
            if not all(field in edu for field in required_fields):
                raise serializers.ValidationError(
                    f"Each education entry must have: {', '.join(required_fields)}"
                )
        return value
    
    def validate_experience(self, value):
        """Validate experience format"""
        if not isinstance(value, list):
            raise serializers.ValidationError("Experience must be a list")
        
        for exp in value:
            required_fields = ['company', 'position', 'start_date']
            if not all(field in exp for field in required_fields):
                raise serializers.ValidationError(
                    f"Each experience entry must have: {', '.join(required_fields)}"
                )
        return value


class ProfileUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating profile"""
    
    class Meta:
        model = Profile
        fields = [
            'bio', 'avatar', 'date_of_birth', 'location',
            'skills', 'education', 'experience', 'certifications', 'languages',
            'linkedin_url', 'github_url', 'portfolio_url'
        ]


class CVSerializer(serializers.ModelSerializer):
    """Serializer for CV documents"""
    
    class Meta:
        model = CV
        fields = [
            'id', 'profile', 'file', 'original_filename', 'file_type',
            'file_size', 'extracted_text', 'extracted_skills',
            'ai_processed', 'ai_processed_at', 'uploaded_at'
        ]
        read_only_fields = [
            'id', 'profile', 'original_filename', 'file_type', 'file_size',
            'extracted_text', 'extracted_skills', 'ai_processed',
            'ai_processed_at', 'uploaded_at'
        ]
        extra_kwargs = {
            'file': {'help_text': 'Stored file reference'},
            'extracted_skills': {'help_text': 'Skills extracted from the CV document'}
        }


class CVUploadSerializer(serializers.Serializer):
    """Serializer for CV upload"""
    
    file = serializers.FileField(required=True, help_text='CV file (.pdf/.doc/.docx). Max size: 10MB')
    
    def validate_file(self, value):
        """Validate CV file"""
        # Check file size (max 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB")
        
        # Check file extension
        allowed_extensions = ['.pdf', '.doc', '.docx']
        ext = value.name.lower().split('.')[-1]
        if f'.{ext}' not in allowed_extensions:
            raise serializers.ValidationError(
                f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
            )
        
        return value


class CertificateSerializer(serializers.ModelSerializer):
    """Serializer for certificates"""
    
    class Meta:
        model = Certificate
        fields = [
            'id', 'profile', 'title', 'issuer', 'issue_date',
            'expiry_date', 'credential_id', 'credential_url',
            'file', 'created_at'
        ]
        read_only_fields = ['id', 'profile', 'created_at']
        extra_kwargs = {
            'title': {'help_text': 'Certificate title or name'},
            'issuer': {'help_text': 'Issuing organization'},
            'issue_date': {'help_text': 'Date of issuance'},
            'expiry_date': {'help_text': 'Optional expiry date'},
            'credential_url': {'help_text': 'URL to credential verification'},
            'file': {'help_text': 'Uploaded certificate file'}
        }


class ProfileStatsSerializer(serializers.Serializer):
    """Serializer for profile statistics"""
    
    total_applications = serializers.IntegerField()
    active_applications = serializers.IntegerField()
    interviews_completed = serializers.IntegerField()
    interviews_scheduled = serializers.IntegerField()
    profile_views = serializers.IntegerField()
    profile_completeness = serializers.FloatField()


class GenerateCVSerializer(serializers.Serializer):
    """Serializer for AI CV generation request"""
    
    template = serializers.ChoiceField(
        choices=['professional', 'modern', 'creative'],
        default='professional'
    )
    template.help_text = 'Select a template style for the generated CV'
    include_photo = serializers.BooleanField(default=True)
    include_photo.help_text = 'Include profile photo in the generated CV'
    sections = serializers.ListField(
        child=serializers.CharField(),
        default=['experience', 'education', 'skills', 'certifications']
    )
    sections.help_text = 'Sections to include in generated CV (overrides defaults)'