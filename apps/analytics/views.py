from rest_framework import generics, views, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Sum, Q, F
from django.utils import timezone
from datetime import timedelta

from .models import RegionStatistics, IndustryStatistics, SkillDemand, ForecastData
from .serializers import (
    RegionStatisticsSerializer,
    IndustryStatisticsSerializer,
    SkillDemandSerializer,
    ForecastDataSerializer,
    DashboardOverviewSerializer,
    RegionMapDataSerializer,
    SkillGapAnalysisSerializer,
    IndustryTrendSerializer
)
from apps.common.permissions import IsGovernment
from apps.jobs.models import Job
from apps.applications.models import Application
from apps.profiles.models import Profile
from .tasks import generate_forecast_data
from drf_spectacular.utils import extend_schema, OpenApiParameter, OpenApiResponse


@extend_schema(
    summary="Government dashboard overview",
    description="High-level government dashboard statistics (requires government role).",
    responses={200: DashboardOverviewSerializer},
    tags=["Analytics"]
)
class DashboardOverviewView(views.APIView):
    """Get dashboard overview stats (government only)"""
    
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get(self, request):
        # Calculate current stats
        total_active_jobs = Job.objects.filter(status='open').count()
        total_candidates = Profile.objects.count()
        total_applications = Application.objects.count()
        
        # Get latest unemployment rate
        latest_stats = RegionStatistics.objects.order_by('-date').first()
        national_unemployment_rate = latest_stats.unemployment_rate if latest_stats else 0
        
        # Calculate avg time to hire
        filled_jobs = Job.objects.filter(status='filled')
        avg_time_to_hire = filled_jobs.aggregate(
            avg=Avg(F('updated_at') - F('created_at'))
        )['avg']
        avg_time_days = avg_time_to_hire.days if avg_time_to_hire else 0
        
        # Jobs filled this month
        this_month = timezone.now().replace(day=1)
        jobs_filled_this_month = Job.objects.filter(
            status='filled',
            updated_at__gte=this_month
        ).count()
        
        stats = {
            'total_active_jobs': total_active_jobs,
            'total_candidates': total_candidates,
            'total_applications': total_applications,
            'national_unemployment_rate': national_unemployment_rate,
            'avg_time_to_hire': avg_time_days,
            'jobs_filled_this_month': jobs_filled_this_month
        }
        
        serializer = DashboardOverviewSerializer(stats)
        return Response(serializer.data)


@extend_schema(
    summary="List region statistics",
    description="List regional statistics. Supports query params region, start_date, end_date.",
    parameters=[
        OpenApiParameter('region', type=str, required=False),
        OpenApiParameter('start_date', type=str, required=False),
        OpenApiParameter('end_date', type=str, required=False),
    ],
    responses={200: RegionStatisticsSerializer(many=True)},
    tags=["Analytics"]
)
class RegionStatisticsView(generics.ListAPIView):
    """List regional statistics"""
    
    serializer_class = RegionStatisticsSerializer
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get_queryset(self):
        queryset = RegionStatistics.objects.all()
        
        # Filter by region
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region=region)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')


@extend_schema(
    summary="Region heatmap data",
    description="Latest per-region statistics used for heatmap displays.",
    responses={200: RegionMapDataSerializer(many=True)},
    tags=["Analytics"]
)
class RegionMapDataView(views.APIView):
    """Get data for region heatmap"""
    
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get(self, request):
        # Get latest stats for each region
        latest_date = RegionStatistics.objects.order_by('-date').first()
        if not latest_date:
            return Response([])
        
        stats = RegionStatistics.objects.filter(date=latest_date.date)
        
        map_data = []
        for stat in stats:
            map_data.append({
                'region': stat.region,
                'jobs_count': stat.active_jobs,
                'candidates_count': stat.active_candidates,
                'unemployment_rate': stat.unemployment_rate or 0,
                'avg_salary': stat.avg_salary or 0
            })
        
        serializer = RegionMapDataSerializer(map_data, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="List industry statistics",
    description="Returns industry-level statistics. Supports industry/start_date/end_date filters.",
    parameters=[
        OpenApiParameter('industry', type=str, required=False),
        OpenApiParameter('start_date', type=str, required=False),
        OpenApiParameter('end_date', type=str, required=False),
    ],
    responses={200: IndustryStatisticsSerializer(many=True)},
    tags=["Analytics"]
)
class IndustryStatisticsView(generics.ListAPIView):
    """List industry statistics"""
    
    serializer_class = IndustryStatisticsSerializer
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get_queryset(self):
        queryset = IndustryStatistics.objects.all()
        
        # Filter by industry
        industry = self.request.query_params.get('industry')
        if industry:
            queryset = queryset.filter(industry=industry)
        
        # Filter by date range
        start_date = self.request.query_params.get('start_date')
        end_date = self.request.query_params.get('end_date')
        
        if start_date:
            queryset = queryset.filter(date__gte=start_date)
        if end_date:
            queryset = queryset.filter(date__lte=end_date)
        
        return queryset.order_by('-date')


@extend_schema(
    summary="List skill demand",
    description="Top skill demand metrics for the marketplace (latest date).",
    responses={200: SkillDemandSerializer(many=True)},
    tags=["Analytics"]
)
class SkillDemandView(generics.ListAPIView):
    """List skill demand data"""
    
    serializer_class = SkillDemandSerializer
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get_queryset(self):
        # Get latest data
        latest_date = SkillDemand.objects.order_by('-date').first()
        if not latest_date:
            return SkillDemand.objects.none()
        
        return SkillDemand.objects.filter(
            date=latest_date.date
        ).order_by('-jobs_requiring')[:20]  # Top 20 skills


@extend_schema(
    summary="Skill gap analysis",
    description="Analyze supply/demand gaps for skills (returns top gaps).",
    responses={200: SkillGapAnalysisSerializer(many=True)},
    tags=["Analytics"]
)
class SkillGapAnalysisView(views.APIView):
    """Analyze skill gaps in the market"""
    
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get(self, request):
        # Get latest skill demand data
        latest_date = SkillDemand.objects.order_by('-date').first()
        if not latest_date:
            return Response([])
        
        skills = SkillDemand.objects.filter(date=latest_date.date)
        
        gap_analysis = []
        for skill in skills:
            gap = skill.jobs_requiring - skill.candidates_having
            gap_percentage = (gap / skill.jobs_requiring * 100) if skill.jobs_requiring > 0 else 0
            
            gap_analysis.append({
                'skill': skill.skill_name,
                'demand': skill.jobs_requiring,
                'supply': skill.candidates_having,
                'gap': gap,
                'gap_percentage': gap_percentage
            })
        
        # Sort by gap percentage (descending)
        gap_analysis.sort(key=lambda x: x['gap_percentage'], reverse=True)
        
        serializer = SkillGapAnalysisSerializer(gap_analysis[:15], many=True)
        return Response(serializer.data)


@extend_schema(
    summary="List forecasts",
    description="List AI-generated forecasts. Supports ?type, ?region, ?industry filters.",
    parameters=[
        OpenApiParameter('type', type=str, required=False),
        OpenApiParameter('region', type=str, required=False),
        OpenApiParameter('industry', type=str, required=False),
    ],
    responses={200: ForecastDataSerializer(many=True)},
    tags=["Analytics"]
)
class ForecastView(generics.ListAPIView):
    """Get AI-generated forecasts"""
    
    serializer_class = ForecastDataSerializer
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get_queryset(self):
        queryset = ForecastData.objects.all()
        
        # Filter by forecast type
        forecast_type = self.request.query_params.get('type')
        if forecast_type:
            queryset = queryset.filter(forecast_type=forecast_type)
        
        # Filter by region
        region = self.request.query_params.get('region')
        if region:
            queryset = queryset.filter(region=region)
        
        # Filter by industry
        industry = self.request.query_params.get('industry')
        if industry:
            queryset = queryset.filter(industry=industry)
        
        return queryset.order_by('-generated_at')


@extend_schema(
    summary="Generate forecast (async)",
    description="Trigger an asynchronous forecast generation job.",
    request=OpenApiResponse(description='forecast_type + optional region/industry/months'),
    responses={202: OpenApiResponse(description='Task started')},
    tags=["Analytics"]
)
class GenerateForecastView(views.APIView):
    """Trigger AI forecast generation"""
    
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def post(self, request):
        forecast_type = request.data.get('forecast_type')
        region = request.data.get('region', '')
        industry = request.data.get('industry', '')
        months = request.data.get('months', 3)
        
        if not forecast_type:
            return Response(
                {'error': 'forecast_type is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Trigger async forecast generation
        task = generate_forecast_data.delay(
            forecast_type=forecast_type,
            region=region,
            industry=industry,
            months=months
        )
        
        return Response({
            'message': 'Forecast generation started',
            'task_id': task.id
        }, status=status.HTTP_202_ACCEPTED)


@extend_schema(
    summary="Industry trend metrics",
    description="Get industry growth rates and trend information for the last period.",
    responses={200: IndustryTrendSerializer(many=True)},
    tags=["Analytics"]
)
class IndustryTrendsView(views.APIView):
    """Get industry trends and growth rates"""
    
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get(self, request):
        # Get data for last 3 months
        three_months_ago = timezone.now() - timedelta(days=90)
        
        current_stats = IndustryStatistics.objects.filter(
            date=timezone.now().date()
        )
        
        old_stats = IndustryStatistics.objects.filter(
            date=three_months_ago.date()
        )
        
        trends = []
        for current in current_stats:
            old = old_stats.filter(industry=current.industry).first()
            
            if old:
                job_growth = current.total_jobs - old.total_jobs
                growth_rate = (job_growth / old.total_jobs * 100) if old.total_jobs > 0 else 0
                
                salary_change = 0
                if current.avg_salary_max and old.avg_salary_max:
                    salary_change = float(
                        (current.avg_salary_max - old.avg_salary_max) / old.avg_salary_max * 100
                    )
                
                trends.append({
                    'industry': current.industry,
                    'growth_rate': growth_rate,
                    'job_growth': job_growth,
                    'avg_salary_change': salary_change
                })
        
        # Sort by growth rate
        trends.sort(key=lambda x: x['growth_rate'], reverse=True)
        
        serializer = IndustryTrendSerializer(trends, many=True)
        return Response(serializer.data)


@extend_schema(
    summary="Export analytics data",
    description="Export analytics CSV for regions or skills. Use ?type=regions|skills.",
    parameters=[OpenApiParameter('type', type=str, required=False, description='regions (default) or skills')],
    responses={200: OpenApiResponse(description='CSV file stream')},
    tags=["Analytics"]
)
class ExportDataView(views.APIView):
    """Export analytics data to CSV"""
    
    permission_classes = [IsAuthenticated, IsGovernment]
    
    def get(self, request):
        import csv
        from django.http import HttpResponse
        
        data_type = request.query_params.get('type', 'regions')
        
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="{data_type}_data.csv"'
        
        writer = csv.writer(response)
        
        if data_type == 'regions':
            writer.writerow([
                'Region', 'Date', 'Active Jobs', 'Active Candidates',
                'Unemployment Rate', 'Avg Salary'
            ])
            
            stats = RegionStatistics.objects.order_by('-date', 'region')[:100]
            for stat in stats:
                writer.writerow([
                    stat.region,
                    stat.date,
                    stat.active_jobs,
                    stat.active_candidates,
                    stat.unemployment_rate,
                    stat.avg_salary
                ])
        
        elif data_type == 'skills':
            writer.writerow([
                'Skill', 'Date', 'Jobs Requiring', 'Candidates Having',
                'Supply/Demand Ratio'
            ])
            
            skills = SkillDemand.objects.order_by('-date', '-jobs_requiring')[:100]
            for skill in skills:
                writer.writerow([
                    skill.skill_name,
                    skill.date,
                    skill.jobs_requiring,
                    skill.candidates_having,
                    skill.supply_demand_ratio
                ])
        
        return response