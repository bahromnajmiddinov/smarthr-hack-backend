from rest_framework import serializers
from .models import RegionStatistics, IndustryStatistics, SkillDemand, ForecastData


class RegionStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for regional statistics"""
    
    class Meta:
        model = RegionStatistics
        fields = [
            'id', 'region', 'date',
            'total_jobs_posted', 'active_jobs', 'filled_positions',
            'total_candidates', 'active_candidates', 'employed_candidates',
            'total_applications', 'successful_applications',
            'unemployment_rate', 'avg_time_to_hire_days', 'avg_salary',
            'created_at', 'updated_at'
        ]
        extra_kwargs = {
            'region': {'help_text': 'Region identifier or name'},
            'date': {'help_text': 'Date for the statistics snapshot'},
            'active_jobs': {'help_text': 'Active job postings count'},
            'unemployment_rate': {'help_text': 'Unemployment rate (percentage)'}
        }


class IndustryStatisticsSerializer(serializers.ModelSerializer):
    """Serializer for industry statistics"""
    
    class Meta:
        model = IndustryStatistics
        fields = [
            'id', 'industry', 'date',
            'total_jobs', 'active_jobs', 'avg_applications_per_job',
            'total_candidates', 'avg_candidate_score',
            'top_skills', 'avg_salary_min', 'avg_salary_max',
            'created_at'
        ]
        extra_kwargs = {
            'industry': {'help_text': 'Industry name or code'},
            'total_jobs': {'help_text': 'Total job postings in the industry'},
            'top_skills': {'help_text': 'List of top skills in the industry'}
        }


class SkillDemandSerializer(serializers.ModelSerializer):
    """Serializer for skill demand data"""
    
    class Meta:
        model = SkillDemand
        fields = [
            'id', 'skill_name', 'date',
            'jobs_requiring', 'candidates_having',
            'supply_demand_ratio', 'avg_salary_premium',
            'created_at'
        ]
        extra_kwargs = {
            'skill_name': {'help_text': 'Canonical skill name'},
            'jobs_requiring': {'help_text': 'Number of jobs requiring the skill'},
            'candidates_having': {'help_text': 'Number of candidates with the skill'}
        }


class ForecastDataSerializer(serializers.ModelSerializer):
    """Serializer for forecast data"""
    
    class Meta:
        model = ForecastData
        fields = [
            'id', 'forecast_type', 'region', 'industry',
            'forecast_date', 'forecast_months',
            'predicted_value', 'confidence_score',
            'forecast_data', 'model_version', 'generated_at'
        ]
        extra_kwargs = {
            'forecast_type': {'help_text': 'Type of forecast (e.g., demand, salary)'},
            'predicted_value': {'help_text': 'Predicted numeric value'},
            'confidence_score': {'help_text': 'Confidence value between 0 and 1'}
        }


class DashboardOverviewSerializer(serializers.Serializer):
    """Serializer for government dashboard overview"""
    
    total_active_jobs = serializers.IntegerField()
    total_candidates = serializers.IntegerField()
    total_applications = serializers.IntegerField()
    national_unemployment_rate = serializers.FloatField()
    national_unemployment_rate.help_text = 'Latest national unemployment rate in percentage'
    avg_time_to_hire = serializers.FloatField()
    jobs_filled_this_month = serializers.IntegerField()


class RegionMapDataSerializer(serializers.Serializer):
    """Serializer for region heatmap data"""
    
    region = serializers.CharField()
    jobs_count = serializers.IntegerField()
    candidates_count = serializers.IntegerField()
    unemployment_rate = serializers.FloatField()
    avg_salary = serializers.DecimalField(max_digits=12, decimal_places=2)
    avg_salary.help_text = 'Average salary in the region'


class SkillGapAnalysisSerializer(serializers.Serializer):
    """Serializer for skill gap analysis"""
    
    skill = serializers.CharField()
    demand = serializers.IntegerField()
    supply = serializers.IntegerField()
    gap = serializers.IntegerField()
    gap_percentage = serializers.FloatField()
    gap_percentage.help_text = 'Gap percentage computed as (demand - supply) / demand * 100'


class IndustryTrendSerializer(serializers.Serializer):
    """Serializer for industry trends"""
    
    industry = serializers.CharField()
    growth_rate = serializers.FloatField()
    job_growth = serializers.IntegerField()
    avg_salary_change = serializers.FloatField()
    avg_salary_change.help_text = 'Percent change in average salaries for the industry period'