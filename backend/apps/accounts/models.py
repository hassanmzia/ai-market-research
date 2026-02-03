import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    """Custom user model for the AI Market Research Assistant."""

    class Role(models.TextChoices):
        ADMIN = 'admin', 'Admin'
        ANALYST = 'analyst', 'Analyst'
        VIEWER = 'viewer', 'Viewer'

    email = models.EmailField(unique=True)
    company = models.CharField(max_length=255, blank=True, default='')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.ANALYST)
    api_key = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    max_daily_research = models.IntegerField(default=10)
    research_count_today = models.IntegerField(default=0)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    preferences = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.email

    def can_research(self):
        """Check if user has remaining research quota for today."""
        return self.research_count_today < self.max_daily_research

    def increment_research_count(self):
        """Increment the daily research count."""
        self.research_count_today += 1
        self.save(update_fields=['research_count_today'])
