from django.conf import settings
from django.db import models


class Notification(models.Model):
    """User notification model."""

    class Type(models.TextChoices):
        RESEARCH_COMPLETE = 'research_complete', 'Research Complete'
        WATCHLIST_ALERT = 'watchlist_alert', 'Watchlist Alert'
        SYSTEM = 'system', 'System'

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    type = models.CharField(max_length=30, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=500)
    message = models.TextField()
    data = models.JSONField(default=dict, blank=True)
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.type}: {self.title}"
