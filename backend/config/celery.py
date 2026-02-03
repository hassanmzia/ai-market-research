"""Celery configuration for AI Market Research Assistant."""
import os

from celery import Celery
from celery.schedules import crontab

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ai_market_research')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'cleanup-old-tasks': {
        'task': 'apps.research.tasks.cleanup_old_tasks',
        'schedule': crontab(hour=0, minute=0),  # Every 24 hours at midnight
    },
    'refresh-watchlist': {
        'task': 'apps.research.tasks.refresh_watchlist',
        'schedule': crontab(hour='*/6', minute=0),  # Every 6 hours
    },
}
app.conf.timezone = 'UTC'
