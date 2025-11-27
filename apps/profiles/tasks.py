from celery import shared_task
from django.utils import timezone
from django.core.files.base import ContentFile
import json

from .models import Profile, CV
from apps.common.ai_service import AIService


@shared_task
def analyze_profile_with_ai(profile_id):
    """Analyze profile and generate AI score"""
    try:
        profile = Profile.objects.get(id=profile_id)
        ai_service = AIService()
        
        # Prepare profile data
        profile_data = {
            'bio': profile.bio,
            'skills': profile.skills,
            'education': profile.education,
            'experience': profile.experience,
            'certifications': profile.certifications,
            'languages': profile.languages
        }
        
        # Get AI analysis
        analysis = ai_service.analyze_profile(profile_data)
        
        # Update profile
        profile.ai_score = analysis.get('score', 0)
        profile.ai_analyzed_at = timezone.now()
        profile.save()
        
        return {
            'success': True,
            'profile_id': str(profile.id),
            'score': profile.ai_score
        }
        
    except Profile.DoesNotExist:
        return {'success': False, 'error': 'Profile not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def extract_cv_data(cv_id):
    """Extract text and skills from CV using AI"""
    try:
        cv = CV.objects.get(id=cv_id)
        ai_service = AIService()
        
        # Extract text from CV
        extracted_data = ai_service.extract_cv_data(cv.file.path)
        
        # Update CV
        cv.extracted_text = extracted_data.get('text', '')
        cv.extracted_skills = extracted_data.get('skills', [])
        cv.ai_processed = True
        cv.ai_processed_at = timezone.now()
        cv.save()
        
        # Update profile with extracted skills
        profile = cv.profile
        existing_skills = set(profile.skills)
        new_skills = set(extracted_data.get('skills', []))
        profile.skills = list(existing_skills.union(new_skills))
        profile.save()
        
        # Trigger profile analysis
        analyze_profile_with_ai.delay(profile.id)
        
        return {
            'success': True,
            'cv_id': cv.id,
            'skills_extracted': len(extracted_data.get('skills', []))
        }
        
    except CV.DoesNotExist:
        return {'success': False, 'error': 'CV not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def generate_cv_pdf(profile_id, template, include_photo, sections):
    """Generate CV PDF from profile data"""
    try:
        profile = Profile.objects.get(id=profile_id)
        ai_service = AIService()
        
        # Prepare profile data
        profile_data = {
            'user': {
                'full_name': profile.user.full_name,
                'email': profile.user.email,
                'phone': profile.user.phone,
            },
            'bio': profile.bio,
            'location': profile.location,
            'skills': profile.skills,
            'education': profile.education,
            'experience': profile.experience,
            'certifications': profile.certifications,
            'languages': profile.languages,
            'linkedin_url': profile.linkedin_url,
            'github_url': profile.github_url,
            'portfolio_url': profile.portfolio_url,
        }
        
        # Generate CV PDF
        pdf_content = ai_service.generate_cv_pdf(
            profile_data,
            template=template,
            include_photo=include_photo,
            sections=sections
        )
        
        # Save as new CV
        cv = CV.objects.create(
            profile=profile,
            original_filename=f'generated_cv_{profile.user.username}.pdf',
            file_type='application/pdf',
            file_size=len(pdf_content),
            ai_processed=True,
            ai_processed_at=timezone.now()
        )
        
        # Save PDF file
        cv.file.save(
            f'cv_{profile.user.username}_{timezone.now().strftime("%Y%m%d")}.pdf',
            ContentFile(pdf_content)
        )
        
        return {
            'success': True,
            'cv_id': cv.id,
            'file_url': cv.file.url
        }
        
    except Profile.DoesNotExist:
        return {'success': False, 'error': 'Profile not found'}
    except Exception as e:
        return {'success': False, 'error': str(e)}