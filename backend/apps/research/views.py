import logging

from django.db.models import Q
from django.utils import timezone
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import (
    ResearchProject,
    ResearchTask,
    CompanyProfile,
    WatchlistItem,
)
from .serializers import (
    ResearchProjectSerializer,
    ResearchProjectCreateSerializer,
    ResearchTaskSerializer,
    ResearchTaskListSerializer,
    ResearchResultSerializer,
    CompanyProfileSerializer,
    WatchlistItemSerializer,
    StartResearchSerializer,
)

logger = logging.getLogger(__name__)


class ResearchProjectViewSet(viewsets.ModelViewSet):
    """CRUD operations for research projects."""
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action in ('create', 'update', 'partial_update'):
            return ResearchProjectCreateSerializer
        return ResearchProjectSerializer

    def get_queryset(self):
        return ResearchProject.objects.filter(
            user=self.request.user
        ).prefetch_related('tasks')

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class ResearchTaskViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve research tasks, plus start new research."""
    permission_classes = [IsAuthenticated]
    lookup_field = 'task_id'
    pagination_class = None

    def get_serializer_class(self):
        if self.action == 'list':
            return ResearchTaskListSerializer
        return ResearchTaskSerializer

    def get_queryset(self):
        return ResearchTask.objects.filter(
            project__user=self.request.user
        ).select_related('project', 'result')

    @action(detail=True, methods=['get'], url_path='result')
    def result(self, request, task_id=None):
        """Return just the research result for a task."""
        task = self.get_object()
        if not hasattr(task, 'result') or task.result is None:
            return Response(
                {'detail': 'Result not available yet.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        return Response(ResearchResultSerializer(task.result).data)

    @action(detail=False, methods=['post'], url_path='start_research')
    def start_research(self, request):
        """Start a new research task for a company."""
        serializer = StartResearchSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)

        user = request.user
        if not user.can_research():
            return Response(
                {'error': 'Daily research quota exceeded. Please try again tomorrow.'},
                status=status.HTTP_429_TOO_MANY_REQUESTS,
            )

        company_name = serializer.validated_data['company_name']
        project_id = serializer.validated_data.get('project_id')

        if project_id:
            project = ResearchProject.objects.get(id=project_id, user=user)
        else:
            project = ResearchProject.objects.create(
                user=user,
                name=f"Research: {company_name}",
                description=f"Auto-created project for {company_name} research.",
                status=ResearchProject.Status.ACTIVE,
            )

        task = ResearchTask.objects.create(
            project=project,
            company_name=company_name,
            status=ResearchTask.Status.PENDING,
        )

        user.increment_research_count()

        # Trigger async Celery task
        from .tasks import run_research_task
        run_research_task.delay(str(task.task_id))

        logger.info(f"Research task {task.task_id} started for company: {company_name}")

        task_data = ResearchTaskSerializer(task).data
        return Response(
            {'task_id': str(task.task_id), 'task': task_data},
            status=status.HTTP_201_CREATED,
        )


class CompanyProfileViewSet(viewsets.ReadOnlyModelViewSet):
    """List and retrieve company profiles."""
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyProfileSerializer
    queryset = CompanyProfile.objects.all()
    filterset_fields = ['sector']
    search_fields = ['name', 'sector', 'description']


class WatchlistViewSet(viewsets.ModelViewSet):
    """CRUD operations for user's watchlist."""
    permission_classes = [IsAuthenticated]
    serializer_class = WatchlistItemSerializer
    pagination_class = None

    def get_queryset(self):
        return WatchlistItem.objects.filter(
            user=self.request.user
        ).select_related('company')

    def create(self, request, *args, **kwargs):
        """Create a watchlist item, accepting company_name instead of company ID."""
        company_name = request.data.get('company_name', '').strip()
        if company_name and 'company' not in request.data:
            company, _ = CompanyProfile.objects.get_or_create(
                name__iexact=company_name,
                defaults={'name': company_name},
            )
            request.data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)
            request.data['company'] = company.id
        return super().create(request, *args, **kwargs)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class CompanySearchView(generics.ListAPIView):
    """Search companies with autocomplete support."""
    permission_classes = [IsAuthenticated]
    serializer_class = CompanyProfileSerializer

    def get_queryset(self):
        query = self.request.query_params.get('q', '').strip()
        if not query:
            return CompanyProfile.objects.none()

        return CompanyProfile.objects.filter(
            Q(name__icontains=query) | Q(sector__icontains=query)
        )[:10]


class ResearchHistoryView(generics.ListAPIView):
    """List all past research tasks for the authenticated user."""
    permission_classes = [IsAuthenticated]
    serializer_class = ResearchTaskListSerializer

    def get_queryset(self):
        queryset = ResearchTask.objects.filter(
            project__user=self.request.user
        ).select_related('project')

        status_filter = self.request.query_params.get('status')
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        company_filter = self.request.query_params.get('company')
        if company_filter:
            queryset = queryset.filter(company_name__icontains=company_filter)

        return queryset
