from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User


class Job(models.Model):
    """Job posting by employers"""
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('open', 'Open'),
        ('closed', 'Closed'),
        ('filled', 'Filled'),
    ]
    
    JOB_TYPE_CHOICES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('internship', 'Internship'),
        ('remote', 'Remote'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    employer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='posted_jobs',
        limit_choices_to={'role': 'employer'}
    )
    
    # Basic info
    title = models.CharField(_('job title'), max_length=255)
    description = models.TextField(_('description'))
    requirements = models.JSONField(_('requirements'), default=list, help_text='List of job requirements')
    responsibilities = models.TextField(_('responsibilities'), blank=True)
    
    # Location & Type
    location = models.CharField(_('location'), max_length=255)
    is_remote = models.BooleanField(_('remote work'), default=False)
    job_type = models.CharField(_('job type'), max_length=20, choices=JOB_TYPE_CHOICES, default='full_time')
    
    # Compensation
    salary_min = models.DecimalField(_('minimum salary'), max_digits=10, decimal_places=2, null=True, blank=True)
    salary_max = models.DecimalField(_('maximum salary'), max_digits=10, decimal_places=2, null=True, blank=True)
    salary_currency = models.CharField(_('currency'), max_length=3, default='UZS')
    
    # Skills & Experience
    required_skills = models.JSONField(_('required skills'), default=list)
    preferred_skills = models.JSONField(_('preferred skills'), default=list)
    experience_years_min = models.IntegerField(_('minimum years of experience'), default=0)
    experience_years_max = models.IntegerField(_('maximum years of experience'), null=True, blank=True)
    
    # Status
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='draft')
    deadline = models.DateTimeField(_('application deadline'), null=True, blank=True)
    
    # Metadata
    views_count = models.IntegerField(_('views count'), default=0)
    applications_count = models.IntegerField(_('applications count'), default=0)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    published_at = models.DateTimeField(_('published at'), null=True, blank=True)
    
    class Meta:
        db_table = 'jobs'
        ordering = ['-created_at']
        verbose_name = _('job')
        verbose_name_plural = _('jobs')
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['location']),
        ]
    
    def __str__(self):
        return f"{self.title} at {self.employer.full_name if self.employer else 'N/A'}"
    
    @property
    def is_active(self):
        return self.status == 'open'


class JobView(models.Model):
    """Track job views for analytics"""
    
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='job_views')
    user = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='viewed_jobs')
    ip_address = models.GenericIPAddressField(_('IP address'), null=True, blank=True)
    viewed_at = models.DateTimeField(_('viewed at'), auto_now_add=True)
    
    class Meta:
        db_table = 'job_views'
        ordering = ['-viewed_at']
    
    def __str__(self):
        return f"{self.job.title} viewed at {self.viewed_at}"