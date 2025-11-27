from django.contrib import admin
from .models import RegionStatistics, IndustryStatistics, SkillDemand, ForecastData


@admin.register(RegionStatistics)
class RegionStatisticsAdmin(admin.ModelAdmin):
    list_display = ['region', 'date', 'active_jobs', 'active_candidates', 'unemployment_rate']
    list_filter = ['region', 'date']
    search_fields = ['region']


@admin.register(IndustryStatistics)
class IndustryStatisticsAdmin(admin.ModelAdmin):
    list_display = ['industry', 'date', 'total_jobs', 'active_jobs']
    list_filter = ['industry', 'date']
    search_fields = ['industry']


@admin.register(SkillDemand)
class SkillDemandAdmin(admin.ModelAdmin):
    list_display = ['skill_name', 'date', 'jobs_requiring', 'candidates_having', 'supply_demand_ratio']
    list_filter = ['date']
    search_fields = ['skill_name']


@admin.register(ForecastData)
class ForecastDataAdmin(admin.ModelAdmin):
    list_display = ['forecast_type', 'region', 'industry', 'forecast_date', 'predicted_value', 'confidence_score']
    list_filter = ['forecast_type', 'region', 'industry']
    readonly_fields = ['generated_at']