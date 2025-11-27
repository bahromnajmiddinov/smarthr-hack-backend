from uuid import uuid4
from django.db import models
from django.utils.translation import gettext_lazy as _
from apps.applications.models import Application
from apps.accounts.models import User


class Interview(models.Model):
    """Interview scheduling and management"""
    
    TYPE_CHOICES = [
        ('phone', 'Phone'),
        ('video', 'Video'),
        ('in_person', 'In Person'),
        ('technical', 'Technical'),
    ]
    
    STATUS_CHOICES = [
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('rescheduled', 'Rescheduled'),
        ('no_show', 'No Show'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    application = models.ForeignKey(Application, on_delete=models.CASCADE, related_name='interviews')
    
    # Interview details
    interview_type = models.CharField(_('type'), max_length=20, choices=TYPE_CHOICES, default='video')
    status = models.CharField(_('status'), max_length=20, choices=STATUS_CHOICES, default='scheduled')
    
    # Scheduling
    scheduled_at = models.DateTimeField(_('scheduled at'))
    duration_minutes = models.IntegerField(_('duration (minutes)'), default=60)
    location = models.CharField(_('location'), max_length=255, blank=True, help_text='Physical location or meeting URL')
    meeting_url = models.URLField(_('meeting URL'), blank=True)
    
    # Participants
    interviewer = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='conducted_interviews'
    )
    
    # Video interview
    video_url = models.URLField(_('video URL'), blank=True, help_text='URL to recorded video interview')
    video_file = models.FileField(_('video file'), upload_to='interview_videos/', null=True, blank=True)
    
    # AI Analysis
    ai_review = models.JSONField(
        _('AI review'), 
        default=dict,
        help_text='AI analysis of video interview (sentiment, keywords, confidence)'
    )
    ai_score = models.FloatField(_('AI score'), null=True, blank=True)
    ai_analyzed_at = models.DateTimeField(_('AI analyzed at'), null=True, blank=True)
    
    # Feedback
    interviewer_feedback = models.TextField(_('interviewer feedback'), blank=True)
    interviewer_rating = models.IntegerField(
        _('interviewer rating'), 
        null=True, 
        blank=True,
        help_text='Rating from 1-10'
    )
    
    # Notes
    notes = models.TextField(_('notes'), blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    completed_at = models.DateTimeField(_('completed at'), null=True, blank=True)
    
    class Meta:
        db_table = 'interviews'
        ordering = ['-scheduled_at']
        verbose_name = _('interview')
        verbose_name_plural = _('interviews')
        indexes = [
            models.Index(fields=['status', 'scheduled_at']),
        ]
    
    def __str__(self):
        return f"Interview for {self.application} at {self.scheduled_at}"
    
    @property
    def is_upcoming(self):
        from django.utils import timezone
        return self.status == 'scheduled' and self.scheduled_at > timezone.now()


class InterviewQuestion(models.Model):
    """Questions asked during interview"""
    
    interview = models.ForeignKey(Interview, on_delete=models.CASCADE, related_name='questions')
    question_text = models.TextField(_('question'))
    answer_text = models.TextField(_('answer'), blank=True)
    ai_score = models.FloatField(_('AI score'), null=True, blank=True)
    order = models.IntegerField(_('order'), default=0)
    
    class Meta:
        db_table = 'interview_questions'
        ordering = ['order']
    
    def __str__(self):
        return f"Q{self.order}: {self.question_text[:50]}"


class InterviewFeedback(models.Model):
    """Candidate feedback about interview experience"""
    
    interview = models.OneToOneField(Interview, on_delete=models.CASCADE, related_name='candidate_feedback')
    rating = models.IntegerField(_('rating'), help_text='Rating from 1-5')
    comments = models.TextField(_('comments'), blank=True)
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'interview_feedback'
    
    def __str__(self):
        return f"Feedback for {self.interview}"