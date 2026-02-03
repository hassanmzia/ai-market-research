import uuid

from django.conf import settings
from django.db import models

from apps.research.models import ResearchTask


class SavedReport(models.Model):
    """A saved report generated from research results."""

    class Format(models.TextChoices):
        MARKDOWN = 'markdown', 'Markdown'
        HTML = 'html', 'HTML'
        PDF = 'pdf', 'PDF'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='saved_reports',
    )
    task = models.ForeignKey(
        ResearchTask,
        on_delete=models.CASCADE,
        related_name='saved_reports',
    )
    title = models.CharField(max_length=500)
    description = models.TextField(blank=True, default='')
    report_data = models.JSONField(default=dict, blank=True)
    format = models.CharField(max_length=20, choices=Format.choices, default=Format.HTML)
    is_public = models.BooleanField(default=False)
    share_token = models.UUIDField(default=uuid.uuid4, unique=True)
    download_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title


class ReportTemplate(models.Model):
    """Templates for generating formatted reports."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    template_content = models.TextField()
    is_default = models.BooleanField(default=False)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='report_templates',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', 'name']

    def __str__(self):
        return self.name
