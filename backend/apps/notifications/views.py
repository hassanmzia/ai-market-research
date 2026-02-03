from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .models import Notification
from .serializers import NotificationSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """List and manage user notifications."""
    permission_classes = [IsAuthenticated]
    serializer_class = NotificationSerializer
    filterset_fields = ['type', 'is_read']

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=['post'], url_path='mark-read')
    def mark_read(self, request, pk=None):
        """Mark a single notification as read."""
        notification = self.get_object()
        notification.is_read = True
        notification.save(update_fields=['is_read'])
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['post'], url_path='mark-all-read')
    def mark_all_read(self, request):
        """Mark all notifications as read for the authenticated user."""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).update(is_read=True)

        return Response({
            'message': f'{count} notifications marked as read.',
            'count': count,
        })

    @action(detail=False, methods=['get'], url_path='unread-count')
    def unread_count(self, request):
        """Get the count of unread notifications."""
        count = Notification.objects.filter(
            user=request.user,
            is_read=False,
        ).count()

        return Response({'unread_count': count})
