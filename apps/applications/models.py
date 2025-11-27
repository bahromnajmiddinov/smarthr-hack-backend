from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.accounts.models import User
from apps.jobs.models import Job


class Application(models.Model):
    """Job application by candidates"""
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted'),
        ('under_review', 'Under Review'),
        ('shortlisted', 'Shortlisted'),
        ('interview_scheduled', 'Interview Scheduled'),
        ('interviewed', 'Interviewed'),
        ('offer_sent', 'Offer Sent'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    job = models.ForeignKey(Job, on_delete=models.CASCADE, related_name='applications')
    user = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='job_applications',
        limit_choices_to={'role': 'candidate'}
    )
    
    # Application details
    cover_letter = models.TextField(_('cover letter'), blank=True)
    cv_file = models.FileField(_('CV file'), upload_to='application_cvs/', null=True, blank=True)
    
    # Status
    status = models.CharField(_('status'), max_length=30, choices=STATUS_CHOICES, default='submitted')
    
    # AI Matching
    ai_match_score = models.FloatField(
        _('AI match score'), 
        null=True, 
        blank=True,
        help_text='AI-calculated match score between candidate and job (0-100)'
    )
    ai_analysis = models.JSONField(
        _('AI analysis'), 
        default=dict,
        help_text='Detailed AI analysis results'
    )
    ai_analyzed_at = models.DateTimeField(_('AI analyzed at'), null=True, blank=True)
    
    # Employer notes
    employer_notes = models.TextField(_('employer notes'), blank=True)
    rejection_reason = models.TextField(_('rejection reason'), blank=True)
    
    # Timestamps
    submitted_at = models.DateTimeField(_('submitted at'), auto_now_add=True)
    reviewed_at = models.DateTimeField(_('reviewed at'), null=True, blank=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'applications'
        ordering = ['-submitted_at']
        verbose_name = _('application')
        verbose_name_plural = _('applications')
        unique_together = [['job', 'user']]
        indexes = [
            models.Index(fields=['status', 'submitted_at']),
            models.Index(fields=['ai_match_score']),
        ]
    
    def __str__(self):
        return f"{self.user.full_name} -> {self.job.title}"
    
    @property
    def is_active(self):
        return self.status not in ['rejected', 'withdrawn', 'accepted']


class ApplicationNote(models.Model):
    """Notes added by employers during review"""
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='notes')
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='application_notes')
    content = models.TextField(_('content'))
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'application_notes'
        ordering = ['created_at']
    
    def __str__(self):
        return f"Note on {self.application} by {self.author.full_name}"


class ApplicationStatusHistory(models.Model):
    """Track status changes for applications"""
    
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='status_history')
    old_status = models.CharField(max_length=30)
    new_status = models.CharField(max_length=30)
    changed_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)
    comment = models.TextField(blank=True)
    changed_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'application_status_history'
        ordering = ['changed_at']
        verbose_name = _('application status history')
        verbose_name_plural = _('application status histories')
    
    def __str__(self):
        return f"{self.old_status} -> {self.new_status}"