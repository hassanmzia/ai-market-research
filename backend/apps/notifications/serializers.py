from rest_framework import serializers

from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for notifications."""

    class Meta:
        model = Notification
        fields = [
            'id', 'type', 'title', 'message', 'data',
            'is_read', 'created_at',
        ]
        read_only_fields = ['id', 'type', 'title', 'message', 'data', 'created_at']
