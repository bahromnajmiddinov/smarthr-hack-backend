from django.urls import path
from .views import (
    DashboardOverviewView,
    RegionStatisticsView,
    RegionMapDataView,
    IndustryStatisticsView,
    SkillDemandView,
    SkillGapAnalysisView,
    ForecastView,
    GenerateForecastView,
    IndustryTrendsView,
    ExportDataView,
)

app_name = 'analytics'

urlpatterns = [
    # Dashboard
    path('dashboard/', DashboardOverviewView.as_view(), name='dashboard_overview'),
    
    # Regional data
    path('regions/', RegionStatisticsView.as_view(), name='region_statistics'),
    path('regions/map/', RegionMapDataView.as_view(), name='region_map_data'),
    
    # Industry data
    path('industries/', IndustryStatisticsView.as_view(), name='industry_statistics'),
    path('industries/trends/', IndustryTrendsView.as_view(), name='industry_trends'),
    
    # Skills
    path('skills/demand/', SkillDemandView.as_view(), name='skill_demand'),
    path('skills/gap/', SkillGapAnalysisView.as_view(), name='skill_gap_analysis'),
    
    # Forecasts
    path('forecast/', ForecastView.as_view(), name='forecast'),
    path('forecast/generate/', GenerateForecastView.as_view(), name='generate_forecast'),
    
    # Export
    path('export/', ExportDataView.as_view(), name='export_data'),
]