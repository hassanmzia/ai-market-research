"""URL configuration for AI Market Research Assistant."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from django.db.models import Count
from django.db.models.functions import TruncMonth

from apps.research.models import ResearchTask, ResearchProject, WatchlistItem, CompanyProfile
from apps.reports.models import SavedReport


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request):
    """Health check endpoint."""
    return Response({
        'status': 'healthy',
        'service': 'ai-market-research-backend',
        'timestamp': timezone.now().isoformat(),
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def dashboard_stats(request):
    """Dashboard statistics for the authenticated user."""
    user = request.user
    user_tasks = ResearchTask.objects.filter(project__user=user)

    total_researches = user_tasks.count()
    completed_researches = user_tasks.filter(status='completed').count()
    active_researches = user_tasks.exclude(
        status__in=['completed', 'failed']
    ).count()
    watchlist_count = WatchlistItem.objects.filter(user=user).count()

    # Recent researches as ResearchTask-shaped objects
    recent_tasks = user_tasks.select_related(
        'project', 'result'
    ).order_by('-created_at')[:5]
    recent_researches = [
        {
            'id': task.pk,
            'task_id': str(task.task_id),
            'project': task.project_id,
            'company_name': task.company_name,
            'status': task.status,
            'progress': task.progress,
            'started_at': task.started_at.isoformat() if task.started_at else None,
            'completed_at': task.completed_at.isoformat() if task.completed_at else None,
            'error_message': task.error_message,
            'created_at': task.created_at.isoformat(),
        }
        for task in recent_tasks
    ]

    # Top sectors from completed research results
    top_sectors = []
    sector_counts = (
        CompanyProfile.objects.filter(
            research_count__gt=0,
        )
        .exclude(sector='')
        .values('sector')
        .annotate(count=Count('id'))
        .order_by('-count')[:5]
    )
    for entry in sector_counts:
        if entry['sector']:
            top_sectors.append({
                'sector': entry['sector'],
                'count': entry['count'],
            })

    # Monthly activity for last 6 months
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    monthly_raw = (
        user_tasks.filter(created_at__gte=six_months_ago)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))
        .order_by('month')
    )
    monthly_activity = [
        {
            'month': entry['month'].strftime('%b %Y'),
            'count': entry['count'],
        }
        for entry in monthly_raw
    ]

    return Response({
        'total_researches': total_researches,
        'completed_researches': completed_researches,
        'active_researches': active_researches,
        'watchlist_count': watchlist_count,
        'recent_researches': recent_researches,
        'top_sectors': top_sectors,
        'monthly_activity': monthly_activity,
    })


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/auth/', include('apps.accounts.urls')),
    path('api/research/', include('apps.research.urls')),
    path('api/reports/', include('apps.reports.urls')),
    path('api/notifications/', include('apps.notifications.urls')),
    path('api/health/', health_check, name='health-check'),
    path('api/dashboard/', dashboard_stats, name='dashboard-stats'),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
