from django.db import models
from django.utils.translation import gettext_lazy as _


class RegionStatistics(models.Model):
    """Regional employment statistics for government dashboard"""
    
    region = models.CharField(_('region'), max_length=100)
    date = models.DateField(_('date'))
    
    # Job market data
    total_jobs_posted = models.IntegerField(_('total jobs posted'), default=0)
    active_jobs = models.IntegerField(_('active jobs'), default=0)
    filled_positions = models.IntegerField(_('filled positions'), default=0)
    
    # Candidate data
    total_candidates = models.IntegerField(_('total candidates'), default=0)
    active_candidates = models.IntegerField(_('active candidates'), default=0)
    employed_candidates = models.IntegerField(_('employed candidates'), default=0)
    
    # Application data
    total_applications = models.IntegerField(_('total applications'), default=0)
    successful_applications = models.IntegerField(_('successful applications'), default=0)
    
    # Unemployment rate
    unemployment_rate = models.FloatField(_('unemployment rate'), null=True, blank=True)
    
    # Average metrics
    avg_time_to_hire_days = models.FloatField(_('average time to hire (days)'), null=True, blank=True)
    avg_salary = models.DecimalField(_('average salary'), max_digits=12, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    updated_at = models.DateTimeField(_('updated at'), auto_now=True)
    
    class Meta:
        db_table = 'region_statistics'
        ordering = ['-date', 'region']
        unique_together = [['region', 'date']]
        verbose_name = _('region statistics')
        verbose_name_plural = _('region statistics')
    
    def __str__(self):
        return f"{self.region} - {self.date}"


class IndustryStatistics(models.Model):
    """Industry-specific employment data"""
    
    industry = models.CharField(_('industry'), max_length=100)
    date = models.DateField(_('date'))
    
    # Demand metrics
    total_jobs = models.IntegerField(_('total jobs'), default=0)
    active_jobs = models.IntegerField(_('active jobs'), default=0)
    avg_applications_per_job = models.FloatField(_('avg applications per job'), null=True, blank=True)
    
    # Supply metrics
    total_candidates = models.IntegerField(_('total candidates'), default=0)
    avg_candidate_score = models.FloatField(_('avg candidate score'), null=True, blank=True)
    
    # Popular skills
    top_skills = models.JSONField(_('top skills'), default=list)
    
    # Salary data
    avg_salary_min = models.DecimalField(_('avg minimum salary'), max_digits=12, decimal_places=2, null=True, blank=True)
    avg_salary_max = models.DecimalField(_('avg maximum salary'), max_digits=12, decimal_places=2, null=True, blank=True)
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'industry_statistics'
        ordering = ['-date', 'industry']
        unique_together = [['industry', 'date']]
        verbose_name = _('industry statistics')
        verbose_name_plural = _('industry statistics')
    
    def __str__(self):
        return f"{self.industry} - {self.date}"


class SkillDemand(models.Model):
    """Track demand for specific skills over time"""
    
    skill_name = models.CharField(_('skill name'), max_length=100)
    date = models.DateField(_('date'))
    
    # Demand indicators
    jobs_requiring = models.IntegerField(_('jobs requiring'), default=0)
    candidates_having = models.IntegerField(_('candidates having'), default=0)
    
    # Gap analysis
    supply_demand_ratio = models.FloatField(
        _('supply/demand ratio'), 
        null=True, 
        blank=True,
        help_text='Ratio of candidates to jobs requiring this skill'
    )
    
    # Salary premium
    avg_salary_premium = models.DecimalField(
        _('avg salary premium'), 
        max_digits=12, 
        decimal_places=2, 
        null=True, 
        blank=True,
        help_text='Average salary difference for jobs requiring this skill'
    )
    
    created_at = models.DateTimeField(_('created at'), auto_now_add=True)
    
    class Meta:
        db_table = 'skill_demand'
        ordering = ['-date', '-jobs_requiring']
        unique_together = [['skill_name', 'date']]
        verbose_name = _('skill demand')
        verbose_name_plural = _('skill demands')
    
    def __str__(self):
        return f"{self.skill_name} - {self.date}"


class ForecastData(models.Model):
    """AI-generated forecasts for job market trends"""
    
    FORECAST_TYPE_CHOICES = [
        ('unemployment', 'Unemployment Rate'),
        ('job_growth', 'Job Growth'),
        ('skill_demand', 'Skill Demand'),
        ('salary_trend', 'Salary Trend'),
    ]
    
    forecast_type = models.CharField(_('forecast type'), max_length=50, choices=FORECAST_TYPE_CHOICES)
    region = models.CharField(_('region'), max_length=100, blank=True)
    industry = models.CharField(_('industry'), max_length=100, blank=True)
    
    # Forecast period
    forecast_date = models.DateField(_('forecast date'))
    forecast_months = models.IntegerField(_('forecast months'), default=3)
    
    # Predictions
    predicted_value = models.FloatField(_('predicted value'))
    confidence_score = models.FloatField(_('confidence score'), help_text='0-1 confidence score')
    
    # Details
    forecast_data = models.JSONField(
        _('forecast data'), 
        default=dict,
        help_text='Detailed forecast breakdown by month'
    )
    
    # Model info
    model_version = models.CharField(_('model version'), max_length=50)
    generated_at = models.DateTimeField(_('generated at'), auto_now_add=True)
    
    class Meta:
        db_table = 'forecast_data'
        ordering = ['-generated_at']
        verbose_name = _('forecast data')
        verbose_name_plural = _('forecast data')
    
    def __str__(self):
        return f"{self.forecast_type} forecast for {self.forecast_date}"