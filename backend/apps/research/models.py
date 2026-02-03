import uuid

from django.conf import settings
from django.db import models


class ResearchProject(models.Model):
    """A collection of research tasks grouped into a project."""

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Draft'
        ACTIVE = 'active', 'Active'
        COMPLETED = 'completed', 'Completed'
        ARCHIVED = 'archived', 'Archived'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='research_projects',
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']

    def __str__(self):
        return f"{self.name} ({self.status})"


class ResearchTask(models.Model):
    """An individual research task for a specific company."""

    class Status(models.TextChoices):
        PENDING = 'pending', 'Pending'
        VALIDATING = 'validating', 'Validating Company'
        ANALYZING_SECTOR = 'analyzing_sector', 'Analyzing Sector'
        FINDING_COMPETITORS = 'finding_competitors', 'Finding Competitors'
        RESEARCHING = 'researching', 'Researching'
        ANALYZING_SENTIMENT = 'analyzing_sentiment', 'Analyzing Sentiment'
        ANALYZING_TRENDS = 'analyzing_trends', 'Analyzing Trends'
        GENERATING_REPORT = 'generating_report', 'Generating Report'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'

    project = models.ForeignKey(
        ResearchProject,
        on_delete=models.CASCADE,
        related_name='tasks',
    )
    company_name = models.CharField(max_length=255)
    task_id = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    status = models.CharField(max_length=30, choices=Status.choices, default=Status.PENDING)
    progress = models.IntegerField(default=0)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Research: {self.company_name} ({self.status})"


class ResearchResult(models.Model):
    """Results from a completed research task."""

    task = models.OneToOneField(
        ResearchTask,
        on_delete=models.CASCADE,
        related_name='result',
    )
    company_validated = models.BooleanField(default=False)
    company_sector = models.CharField(max_length=255, blank=True, default='')
    competitors = models.JSONField(default=list, blank=True)
    financial_data = models.JSONField(default=dict, blank=True)
    market_research = models.JSONField(default=dict, blank=True)
    sentiment_data = models.JSONField(default=dict, blank=True)
    trend_data = models.JSONField(default=dict, blank=True)
    report_markdown = models.TextField(blank=True, default='')
    report_html = models.TextField(blank=True, default='')
    executive_summary = models.TextField(blank=True, default='')
    swot_analysis = models.JSONField(default=dict, blank=True)
    recommendations = models.JSONField(default=list, blank=True)
    raw_agent_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"Result for {self.task.company_name}"


class CompanyProfile(models.Model):
    """Cached company profile information."""

    name = models.CharField(max_length=255, unique=True)
    sector = models.CharField(max_length=255, blank=True, default='')
    description = models.TextField(blank=True, default='')
    website = models.URLField(blank=True, default='')
    logo_url = models.URLField(blank=True, default='')
    last_researched = models.DateTimeField(null=True, blank=True)
    research_count = models.IntegerField(default=0)
    cached_data = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class WatchlistItem(models.Model):
    """User's watchlist entry for a company."""

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='watchlist_items',
    )
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name='watchers',
    )
    alert_on_news = models.BooleanField(default=True)
    alert_on_competitor_change = models.BooleanField(default=False)
    notes = models.TextField(blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        unique_together = ['user', 'company']

    def __str__(self):
        return f"{self.user.email} watching {self.company.name}"
