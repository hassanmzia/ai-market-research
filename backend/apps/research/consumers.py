import json
import logging

from channels.generic.websocket import AsyncWebsocketConsumer

logger = logging.getLogger(__name__)


class ResearchProgressConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time research task progress updates."""

    async def connect(self):
        self.task_id = self.scope['url_route']['kwargs']['task_id']
        self.group_name = f'research_{self.task_id}'

        # Join the task-specific group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name,
        )

        await self.accept()

        # Send initial connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'task_id': self.task_id,
            'message': 'Connected to research progress updates.',
        }))

        logger.info(f"WebSocket connected for task {self.task_id}")

    async def disconnect(self, close_code):
        # Leave the task-specific group
        await self.channel_layer.group_discard(
            self.group_name,
            self.channel_name,
        )
        logger.info(f"WebSocket disconnected for task {self.task_id} (code: {close_code})")

    async def receive(self, text_data):
        """Handle incoming messages from the WebSocket client."""
        try:
            data = json.loads(text_data)
            message_type = data.get('type', '')

            if message_type == 'ping':
                await self.send(text_data=json.dumps({
                    'type': 'pong',
                    'task_id': self.task_id,
                }))
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': 'Invalid JSON received.',
            }))

    async def research_progress(self, event):
        """Handle research progress updates from the channel layer."""
        await self.send(text_data=json.dumps({
            'type': 'research_progress',
            'status': event.get('status', ''),
            'progress': event.get('progress', 0),
            'company_name': event.get('company_name', ''),
            'error_message': event.get('error_message', ''),
        }))
