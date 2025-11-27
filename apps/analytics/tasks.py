from celery import shared_task
from django.utils import timezone
from django.db.models import Count, Avg
from datetime import timedelta

from .models import RegionStatistics, IndustryStatistics, SkillDemand, ForecastData
from apps.jobs.models import Job
from apps.applications.models import Application
from apps.profiles.models import Profile
from apps.common.ai_service import AIService


@shared_task
def update_regional_statistics():
    """Update regional statistics (run daily)"""
    try:
        today = timezone.now().date()
        regions = ['Tashkent', 'Samarkand', 'Bukhara', 'Andijan', 'Namangan', 
                   'Fergana', 'Kashkadarya', 'Surkhandarya', 'Khorezm', 
                   'Navoi', 'Jizzakh', 'Syrdarya', 'Karakalpakstan']
        
        for region in regions:
            # Calculate stats for region
            jobs_in_region = Job.objects.filter(location__icontains=region)
            
            stats, created = RegionStatistics.objects.update_or_create(
                region=region,
                date=today,
                defaults={
                    'total_jobs_posted': jobs_in_region.count(),
                    'active_jobs': jobs_in_region.filter(status='open').count(),
                    'filled_positions': jobs_in_region.filter(status='filled').count(),
                    'total_candidates': Profile.objects.filter(location__icontains=region).count(),
                    'active_candidates': Profile.objects.filter(
                        location__icontains=region,
                        user__job_applications__isnull=False
                    ).distinct().count(),
                    'total_applications': Application.objects.filter(
                        job__location__icontains=region
                    ).count(),
                }
            )
        
        return {'success': True, 'regions_updated': len(regions)}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def update_industry_statistics():
    """Update industry statistics (run daily)"""
    try:
        today = timezone.now().date()
        
        # Get all unique industries from job descriptions
        industries = ['IT', 'Finance', 'Healthcare', 'Education', 'Manufacturing',
                      'Retail', 'Construction', 'Transportation', 'Hospitality']
        
        for industry in industries:
            jobs = Job.objects.filter(description__icontains=industry)
            
            IndustryStatistics.objects.update_or_create(
                industry=industry,
                date=today,
                defaults={
                    'total_jobs': jobs.count(),
                    'active_jobs': jobs.filter(status='open').count(),
                    'avg_applications_per_job': jobs.aggregate(
                        avg=Avg('applications_count')
                    )['avg'] or 0,
                }
            )
        
        return {'success': True, 'industries_updated': len(industries)}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def update_skill_demand():
    """Update skill demand data (run daily)"""
    try:
        today = timezone.now().date()
        
        # Get all skills from jobs
        all_jobs = Job.objects.filter(status='open')
        skill_counts = {}
        
        for job in all_jobs:
            for skill in job.required_skills:
                skill_counts[skill] = skill_counts.get(skill, 0) + 1
        
        # Get skill supply from profiles
        profiles = Profile.objects.all()
        skill_supply = {}
        
        for profile in profiles:
            for skill in profile.skills:
                skill_supply[skill] = skill_supply.get(skill, 0) + 1
        
        # Create/update SkillDemand records
        for skill, demand in skill_counts.items():
            supply = skill_supply.get(skill, 0)
            ratio = supply / demand if demand > 0 else 0
            
            SkillDemand.objects.update_or_create(
                skill_name=skill,
                date=today,
                defaults={
                    'jobs_requiring': demand,
                    'candidates_having': supply,
                    'supply_demand_ratio': ratio
                }
            )
        
        return {'success': True, 'skills_updated': len(skill_counts)}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}


@shared_task
def generate_forecast_data(forecast_type, region='', industry='', months=3):
    """Generate AI-powered forecasts"""
    try:
        ai_service = AIService()
        
        # Get historical data
        historical_data = []
        if forecast_type == 'unemployment':
            stats = RegionStatistics.objects.filter(region=region).order_by('-date')[:12]
            historical_data = [
                {'date': str(s.date), 'value': s.unemployment_rate or 0}
                for s in stats
            ]
        elif forecast_type == 'job_growth':
            if region:
                stats = RegionStatistics.objects.filter(region=region).order_by('-date')[:12]
                historical_data = [
                    {'date': str(s.date), 'value': s.total_jobs_posted}
                    for s in stats
                ]
            elif industry:
                stats = IndustryStatistics.objects.filter(industry=industry).order_by('-date')[:12]
                historical_data = [
                    {'date': str(s.date), 'value': s.total_jobs}
                    for s in stats
                ]
        
        # Generate forecast
        forecast = ai_service.generate_forecast(
            forecast_type=forecast_type,
            historical_data=historical_data,
            months=months
        )
        
        # Save forecast
        forecast_obj = ForecastData.objects.create(
            forecast_type=forecast_type,
            region=region,
            industry=industry,
            forecast_date=timezone.now().date(),
            forecast_months=months,
            predicted_value=forecast['predicted_value'],
            confidence_score=forecast['confidence'],
            forecast_data=forecast['monthly_data'],
            model_version='v1.0'
        )
        
        return {
            'success': True,
            'forecast_id': forecast_obj.id,
            'predicted_value': forecast['predicted_value']
        }
        
    except Exception as e:
        return {'success': False, 'error': str(e)}