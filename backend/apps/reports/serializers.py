from rest_framework import serializers

from .models import SavedReport, ReportTemplate


class SavedReportSerializer(serializers.ModelSerializer):
    """Serializer for saved reports."""
    task_company = serializers.CharField(source='task.company_name', read_only=True)
    share_url = serializers.SerializerMethodField()

    class Meta:
        model = SavedReport
        fields = [
            'id', 'task', 'task_company', 'title', 'description',
            'report_data', 'format', 'is_public', 'share_token',
            'share_url', 'download_count', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'share_token', 'download_count', 'created_at', 'updated_at']

    def get_share_url(self, obj):
        if obj.is_public:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(f'/api/reports/shared/{obj.share_token}/')
        return None


class SavedReportCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating saved reports."""

    class Meta:
        model = SavedReport
        fields = ['task', 'title', 'description', 'report_data', 'format', 'is_public']
        extra_kwargs = {
            'description': {'required': False, 'default': ''},
            'report_data': {'required': False, 'default': dict},
            'format': {'required': False, 'default': 'markdown'},
            'is_public': {'required': False, 'default': False},
        }

    def validate_task(self, value):
        request = self.context.get('request')
        if request and hasattr(request, 'user'):
            if value.project.user != request.user:
                raise serializers.ValidationError("Task does not belong to you.")
        return value


class ReportTemplateSerializer(serializers.ModelSerializer):
    """Serializer for report templates."""

    class Meta:
        model = ReportTemplate
        fields = [
            'id', 'name', 'description', 'template_content',
            'is_default', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
