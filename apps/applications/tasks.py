from celery import shared_task
from django.utils import timezone

from .models import Application
from apps.common.ai_service import AIService


@shared_task
def calculate_ai_match_score(application_id):
    """Calculate AI match score between candidate and job"""
    try:
        application = Application.objects.select_related(
            'user', 'user__profile', 'job'
        ).get(id=application_id)
        
        ai_service = AIService()
        
        # Prepare candidate data
        profile = application.user.profile
        candidate_data = {
            'skills': profile.skills,
            'education': profile.education,
            'experience': profile.experience,
            'certifications': profile.certifications,
            'languages': profile.languages
        }
        
        # Prepare job requirements
        job_requirements = {
            'title': application.job.title,
            'description': application.job.description,
            'requirements': application.job.requirements,
            'required_skills': application.job.required_skills,
            'preferred_skills': application.job.preferred_skills,
            'experience_years_min': application.job.experience_years_min,
            'experience_years_max': application.job.experience_years_max
        }
        
        # Calculate match
        match_result = ai_service.calculate_match_score(
            candidate_data,
            job_requirements
        )
        
        # Update application
        application.ai_match_score = match_result['score']
        application.ai_analysis = match_result['analysis']
        application.ai_analyzed_at = timezone.now()
        application.save()
        
        return {
            'success': True,
            'application_id': str(application.id),
            'match_score': application.ai_match_score
        }
        
    except Application.DoesNotExist:
        return {'success': False, 'error': 'Application not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def send_application_notification(application_id):
    """Send notification to employer about new application"""
    try:
        application = Application.objects.select_related(
            'user', 'job', 'job__employer'
        ).get(id=application_id)
        
        # TODO: Implement email/SMS notification
        # For now, just return success
        
        return {
            'success': True,
            'application_id': str(application.id)
        }
        
    except Application.DoesNotExist:
        return {'success': False, 'error': 'Application not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}