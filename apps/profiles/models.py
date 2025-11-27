from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User


class Profile(models.Model):
    """User profile with skills and experience"""
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(_('biography'), blank=True)
    avatar = models.ImageField(_('avatar'), upload_to='avatars/', null=True, blank=True)
    date_of_birth = models.DateField(_('date of birth'), null=True, blank=True)
    location = models.CharField(_('location'), max_length=255, blank=True)
    
    # Structured data
    skills = models.JSONField(_('skills'), default=list, help_text='List of skills')
    education = models.JSONField(_('education'), default=list, help_text='Education history')
    experience = models.JSONField(_('experience'), default=list, help_text='Work experience')
    certifications = models.JSONField(_('certifications'), default=list)
    languages = models.JSONField(_('languages'), default=list)
    
    # AI-generated score
    ai_score = models.FloatField(_('AI score'), null=True, blank=True, help_text='AI-generated profile quality score')
    ai_analyzed_at = models.DateTimeField(_('AI analyzed at'), null=True, blank=True)
    
    # Social links
    linkedin_url = models.URLField(_('LinkedIn URL'), blank=True)
    github_url = models.URLField(_('GitHub URL'), blank=True)
    portfolio_url = models.URLField(_('Portfolio URL'), blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'profiles'
        ordering = ['-created_at']
        verbose_name = _('profile')
        verbose_name_plural = _('profiles')
    
    def __str__(self):
        return f"Profile of {self.user.full_name}"


class CV(models.Model):
    """Uploaded CV documents"""
    
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='cvs')
    file = models.FileField(_('CV file'), upload_to='cvs/')
    original_filename = models.CharField(_('original filename'), max_length=255)
    file_type = models.CharField(_('file type'), max_length=50)
    file_size = models.IntegerField(_('file size'))
    
    # AI extraction results
    extracted_text = models.TextField(_('extracted text'), blank=True)
    extracted_skills = models.JSONField(_('extracted skills'), default=list)
    ai_processed = models.BooleanField(_('AI processed'), default=False)
    ai_processed_at = models.DateTimeField(_('AI processed at'), null=True, blank=True)
    
    uploaded_at = models.DateTimeField(_('uploaded at'), auto_now_add=True)
    
    class Meta:
        db_table = 'cvs'
        ordering = ['-uploaded_at']
        verbose_name = _('CV')
        verbose_name_plural = _('CVs')
    
    def __str__(self):
        return f"CV - {self.original_filename}"


class Certificate(models.Model):
    """Professional certificates"""
    
    profile = models.ForeignKey(Profile, on_delete=models.CASCADE, related_name='certificates')
    title = models.CharField(_('title'), max_length=255)
    issuer = models.CharField(_('issuer'), max_length=255)
    issue_date = models.DateField(_('issue date'))
    expiry_date = models.DateField(_('expiry date'), null=True, blank=True)
    credential_id = models.CharField(_('credential ID'), max_length=255, blank=True)
    credential_url = models.URLField(_('credential URL'), blank=True)
    file = models.FileField(_('certificate file'), upload_to='certificates/', null=True, blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'certificates'
        ordering = ['-issue_date']
        verbose_name = _('certificate')
        verbose_name_plural = _('certificates')
    
    def __str__(self):
        return f"{self.title} - {self.issuer}"