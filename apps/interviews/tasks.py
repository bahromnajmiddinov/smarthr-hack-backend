from celery import shared_task
from django.utils import timezone

from .models import Interview
from apps.common.ai_service import AIService


@shared_task
def analyze_interview_video(interview_id):
    """Analyze interview video using AI"""
    try:
        interview = Interview.objects.get(id=interview_id)
        
        if not interview.video_file:
            return {'success': False, 'error': 'No video file found'}
        
        ai_service = AIService()
        
        # Analyze video
        analysis = ai_service.analyze_interview_video(interview.video_file.path)
        
        # Update interview
        interview.ai_review = analysis.get('review', {})
        interview.ai_score = analysis.get('score', 0)
        interview.ai_analyzed_at = timezone.now()
        interview.save()
        
        return {
            'success': True,
            'interview_id': str(interview.id),
            'ai_score': interview.ai_score
        }
        
    except Interview.DoesNotExist:
        return {'success': False, 'error': 'Interview not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def send_interview_reminders():
    """Send reminders for upcoming interviews (run daily)"""
    from datetime import timedelta
    
    # Get interviews scheduled for tomorrow
    tomorrow = timezone.now() + timedelta(days=1)
    interviews = Interview.objects.filter(
        status='scheduled',
        scheduled_at__date=tomorrow.date()
    )
    
    reminder_count = 0
    for interview in interviews:
        # TODO: Send email/SMS reminder
        reminder_count += 1
    
    return {
        'success': True,
        'reminders_sent': reminder_count
    }