import logging
import time

import httpx
import markdown
from celery import shared_task
from django.conf import settings
from django.utils import timezone

logger = logging.getLogger(__name__)

A2A_ORCHESTRATOR_URL = getattr(settings, 'A2A_ORCHESTRATOR_URL', 'http://localhost:8060')

STATUS_STAGES = [
    ('validating', 10),
    ('analyzing_sector', 25),
    ('finding_competitors', 40),
    ('researching', 55),
    ('analyzing_sentiment', 70),
    ('analyzing_trends', 85),
    ('generating_report', 95),
]


def _update_task_status(task, status_value, progress, error_message=''):
    """Update task status and send WebSocket notification."""
    task.status = status_value
    task.progress = progress
    if error_message:
        task.error_message = error_message
    task.save(update_fields=['status', 'progress', 'error_message'])

    # Send WebSocket notification via Redis channel layer
    try:
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync

        channel_layer = get_channel_layer()
        if channel_layer:
            async_to_sync(channel_layer.group_send)(
                f'research_{task.task_id}',
                {
                    'type': 'research_progress',
                    'status': status_value,
                    'progress': progress,
                    'company_name': task.company_name,
                    'error_message': error_message,
                }
            )
    except Exception as e:
        logger.warning(f"Failed to send WebSocket update for task {task.task_id}: {e}")


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def run_research_task(self, task_id):
    """
    Main research task that calls the A2A orchestrator.
    Updates task status at each stage and stores results.
    """
    from .models import ResearchTask, ResearchResult, CompanyProfile

    try:
        task = ResearchTask.objects.get(task_id=task_id)
    except ResearchTask.DoesNotExist:
        logger.error(f"Research task {task_id} not found.")
        return

    task.started_at = timezone.now()
    task.save(update_fields=['started_at'])

    logger.info(f"Starting research for task {task_id}: {task.company_name}")

    try:
        # Step 1: Call A2A orchestrator to start research
        _update_task_status(task, 'validating', 5)

        with httpx.Client(timeout=300.0) as client:
            # Initiate research with the A2A orchestrator
            response = client.post(
                f"{A2A_ORCHESTRATOR_URL}/a2a/research",
                json={
                    'company_name': task.company_name,
                    'task_id': str(task.task_id),
                },
            )

            if response.status_code != 200 and response.status_code != 202:
                raise Exception(f"A2A orchestrator returned status {response.status_code}: {response.text}")

            orchestrator_data = response.json()
            orchestrator_task_id = orchestrator_data.get('task_id', str(task.task_id))

            # Step 2: Poll for progress updates
            max_polls = 120  # Max ~10 minutes of polling
            poll_interval = 5  # 5 seconds between polls

            for poll_count in range(max_polls):
                time.sleep(poll_interval)

                try:
                    status_response = client.get(
                        f"{A2A_ORCHESTRATOR_URL}/a2a/research/{orchestrator_task_id}/status",
                    )

                    if status_response.status_code != 200:
                        logger.warning(
                            f"Status poll returned {status_response.status_code} "
                            f"for task {task_id}"
                        )
                        continue

                    status_data = status_response.json()
                    current_status = status_data.get('status', 'researching')
                    current_progress = status_data.get('progress', 0)

                    # Map orchestrator status to our stages
                    for stage_name, stage_progress in STATUS_STAGES:
                        if current_status == stage_name:
                            _update_task_status(task, stage_name, stage_progress)
                            break
                    else:
                        if current_progress > 0:
                            _update_task_status(task, task.status, min(current_progress, 95))

                    # Check for completion
                    if current_status == 'completed':
                        break
                    elif current_status == 'failed':
                        error_msg = status_data.get('error', 'Research failed in orchestrator.')
                        raise Exception(error_msg)

                except httpx.RequestError as e:
                    logger.warning(f"Poll request failed for task {task_id}: {e}")
                    continue

            # Step 3: Fetch final results
            _update_task_status(task, 'generating_report', 95)

            result_response = client.get(
                f"{A2A_ORCHESTRATOR_URL}/a2a/research/{orchestrator_task_id}/result",
            )

            if result_response.status_code != 200:
                raise Exception(f"Failed to fetch results: {result_response.status_code}")

            result_data = result_response.json()

        # Step 4: Store results
        report_md = result_data.get('report_markdown', '')
        report_html = markdown.markdown(report_md, extensions=['tables', 'fenced_code']) if report_md else ''

        research_result = ResearchResult.objects.create(
            task=task,
            company_validated=result_data.get('company_validated', False),
            company_sector=result_data.get('company_sector', ''),
            competitors=result_data.get('competitors', []),
            financial_data=result_data.get('financial_data', {}),
            market_research=result_data.get('market_research', {}),
            sentiment_data=result_data.get('sentiment_data', {}),
            trend_data=result_data.get('trend_data', {}),
            report_markdown=report_md,
            report_html=report_html,
            executive_summary=result_data.get('executive_summary', ''),
            swot_analysis=result_data.get('swot_analysis', {}),
            recommendations=result_data.get('recommendations', []),
            raw_agent_data=result_data,
        )

        # Update or create company profile cache
        company_profile, _ = CompanyProfile.objects.update_or_create(
            name=task.company_name,
            defaults={
                'sector': result_data.get('company_sector', ''),
                'description': result_data.get('executive_summary', '')[:500],
                'website': result_data.get('website', ''),
                'logo_url': result_data.get('logo_url', ''),
                'last_researched': timezone.now(),
                'cached_data': {
                    'sector': result_data.get('company_sector', ''),
                    'competitors': result_data.get('competitors', [])[:5],
                },
            },
        )
        company_profile.research_count += 1
        company_profile.save(update_fields=['research_count'])

        # Mark task as completed
        task.status = 'completed'
        task.progress = 100
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'progress', 'completed_at'])

        _update_task_status(task, 'completed', 100)

        # Create notification for the user
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=task.project.user,
                type='research_complete',
                title=f'Research Complete: {task.company_name}',
                message=f'Your research on {task.company_name} has been completed successfully.',
                data={
                    'task_id': str(task.task_id),
                    'company_name': task.company_name,
                    'project_id': task.project.id,
                },
            )
        except Exception as e:
            logger.warning(f"Failed to create notification for task {task_id}: {e}")

        logger.info(f"Research task {task_id} completed successfully for {task.company_name}")

    except Exception as exc:
        logger.error(f"Research task {task_id} failed: {exc}", exc_info=True)

        task.status = 'failed'
        task.error_message = str(exc)[:2000]
        task.completed_at = timezone.now()
        task.save(update_fields=['status', 'error_message', 'completed_at'])

        _update_task_status(task, 'failed', task.progress, str(exc)[:500])

        # Create failure notification
        try:
            from apps.notifications.models import Notification
            Notification.objects.create(
                user=task.project.user,
                type='research_complete',
                title=f'Research Failed: {task.company_name}',
                message=f'Your research on {task.company_name} has failed. Error: {str(exc)[:200]}',
                data={
                    'task_id': str(task.task_id),
                    'company_name': task.company_name,
                    'error': str(exc)[:500],
                },
            )
        except Exception:
            pass

        # Retry on transient errors
        if isinstance(exc, (httpx.RequestError, httpx.TimeoutException)):
            raise self.retry(exc=exc)


@shared_task
def cleanup_old_tasks():
    """Remove research tasks older than 30 days."""
    from .models import ResearchTask

    cutoff_date = timezone.now() - timezone.timedelta(days=30)
    old_tasks = ResearchTask.objects.filter(
        created_at__lt=cutoff_date,
        status__in=['completed', 'failed'],
    )
    count = old_tasks.count()
    old_tasks.delete()
    logger.info(f"Cleaned up {count} old research tasks.")
    return count


@shared_task
def refresh_watchlist():
    """Refresh data for all companies on user watchlists."""
    from .models import WatchlistItem, CompanyProfile

    watched_companies = CompanyProfile.objects.filter(
        watchers__isnull=False
    ).distinct()

    refreshed = 0
    for company in watched_companies:
        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(
                    f"{A2A_ORCHESTRATOR_URL}/a2a/company/refresh",
                    json={'company_name': company.name},
                )

                if response.status_code == 200:
                    data = response.json()
                    company.cached_data = data
                    company.last_researched = timezone.now()
                    company.save(update_fields=['cached_data', 'last_researched'])
                    refreshed += 1

                    # Notify watchers if there are significant changes
                    if data.get('has_significant_changes', False):
                        watchers = WatchlistItem.objects.filter(
                            company=company,
                            alert_on_news=True,
                        ).select_related('user')

                        from apps.notifications.models import Notification
                        for watcher in watchers:
                            Notification.objects.create(
                                user=watcher.user,
                                type='watchlist_alert',
                                title=f'Watchlist Alert: {company.name}',
                                message=f'Significant changes detected for {company.name}.',
                                data={
                                    'company_name': company.name,
                                    'company_id': company.id,
                                    'changes': data.get('changes', {}),
                                },
                            )

        except Exception as e:
            logger.error(f"Failed to refresh watchlist company {company.name}: {e}")

    logger.info(f"Refreshed {refreshed} watchlist companies.")
    return refreshed
