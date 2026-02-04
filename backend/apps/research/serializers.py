from rest_framework import serializers

from .models import (
    ResearchProject,
    ResearchTask,
    ResearchResult,
    CompanyProfile,
    WatchlistItem,
)


class ResearchResultSerializer(serializers.ModelSerializer):
    """Serializer for research results."""

    class Meta:
        model = ResearchResult
        fields = [
            'id', 'company_validated', 'company_sector', 'competitors',
            'financial_data', 'market_research', 'sentiment_data',
            'trend_data', 'report_markdown', 'report_html',
            'executive_summary', 'swot_analysis', 'recommendations',
            'raw_agent_data', 'created_at',
        ]
        read_only_fields = fields


class ResearchTaskSerializer(serializers.ModelSerializer):
    """Serializer for research tasks with nested result."""
    result = ResearchResultSerializer(read_only=True)

    class Meta:
        model = ResearchTask
        fields = [
            'id', 'project', 'company_name', 'task_id', 'status',
            'progress', 'started_at', 'completed_at', 'error_message',
            'created_at', 'result',
        ]
        read_only_fields = [
            'id', 'task_id', 'status', 'progress', 'started_at',
            'completed_at', 'error_message', 'created_at',
        ]


class ResearchTaskListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for task listing (no nested result)."""

    class Meta:
        model = ResearchTask
        fields = [
            'id', 'project', 'company_name', 'task_id', 'status',
            'progress', 'started_at', 'completed_at', 'error_message',
            'created_at',
        ]
        read_only_fields = fields


class ResearchProjectSerializer(serializers.ModelSerializer):
    """Serializer for research projects with nested tasks."""
    tasks = ResearchTaskListSerializer(many=True, read_only=True)
    task_count = serializers.SerializerMethodField()

    class Meta:
        model = ResearchProject
        fields = [
            'id', 'name', 'description', 'status',
            'created_at', 'updated_at', 'tasks', 'task_count',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def get_task_count(self, obj):
        return obj.tasks.count()


class ResearchProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating research projects."""

    class Meta:
        model = ResearchProject
        fields = ['id', 'name', 'description', 'status']
        read_only_fields = ['id']


class CompanyProfileSerializer(serializers.ModelSerializer):
    """Serializer for company profiles."""

    class Meta:
        model = CompanyProfile
        fields = [
            'id', 'name', 'sector', 'description', 'website',
            'logo_url', 'last_researched', 'research_count',
            'cached_data', 'created_at', 'updated_at',
        ]
        read_only_fields = fields


class WatchlistItemSerializer(serializers.ModelSerializer):
    """Serializer for watchlist items."""
    company = CompanyProfileSerializer(read_only=True)

    class Meta:
        model = WatchlistItem
        fields = [
            'id', 'company',
            'alert_on_news', 'alert_on_competitor_change',
            'notes', 'created_at',
        ]
        read_only_fields = ['id', 'created_at']


class StartResearchSerializer(serializers.Serializer):
    """Serializer for starting a new research task."""
    company_name = serializers.CharField(max_length=255, required=True)
    project_id = serializers.IntegerField(required=False)

    def validate_company_name(self, value):
        value = value.strip()
        if len(value) < 2:
            raise serializers.ValidationError("Company name must be at least 2 characters.")
        return value

    def validate_project_id(self, value):
        user = self.context['request'].user
        if not ResearchProject.objects.filter(id=value, user=user).exists():
            raise serializers.ValidationError("Project not found or does not belong to you.")
        return value
