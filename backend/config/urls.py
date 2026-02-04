"""URL configuration for AI Market Research Assistant."""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from django.utils import timezone

from apps.research.models import ResearchTask, ResearchProject
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
    total_projects = ResearchProject.objects.filter(user=user).count()
    active_projects = ResearchProject.objects.filter(user=user, status='active').count()
    total_tasks = ResearchTask.objects.filter(project__user=user).count()
    completed_tasks = ResearchTask.objects.filter(project__user=user, status='completed').count()
    failed_tasks = ResearchTask.objects.filter(project__user=user, status='failed').count()
    pending_tasks = ResearchTask.objects.filter(
        project__user=user,
    ).exclude(
        status__in=['completed', 'failed']
    ).count()
    saved_reports = SavedReport.objects.filter(user=user).count()
    recent_tasks = ResearchTask.objects.filter(
        project__user=user
    ).select_related('project').order_by('-created_at')[:5]

    recent_tasks_data = [
        {
            'id': str(task.task_id),
            'company_name': task.company_name,
            'status': task.status,
            'progress': task.progress,
            'project_name': task.project.name,
            'created_at': task.created_at.isoformat(),
        }
        for task in recent_tasks
    ]

    return Response({
        'total_projects': total_projects,
        'active_projects': active_projects,
        'total_tasks': total_tasks,
        'completed_tasks': completed_tasks,
        'failed_tasks': failed_tasks,
        'pending_tasks': pending_tasks,
        'saved_reports': saved_reports,
        'recent_tasks': recent_tasks_data,
        'research_quota': {
            'used': user.research_count_today,
            'max': user.max_daily_research,
        },
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
