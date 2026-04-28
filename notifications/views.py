"""API views for the notification service."""
import logging

from django.db.models import Count
from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .metrics import notifications_received_total
from .models import Notification
from .serializers import NotificationSerializer, SendNotificationSerializer
from .services.dispatcher import create_and_dispatch, dispatch

logger = logging.getLogger('notifications')


class NotificationViewSet(viewsets.ModelViewSet):
    """CRUD + custom actions for notifications.

    Other microservices (Order, Payment, Catalog) should call `POST /send/`
    rather than creating raw notifications via the standard create endpoint.
    """
    queryset = Notification.objects.all()
    serializer_class = NotificationSerializer
    filterset_fields = ['status', 'type', 'channel', 'user_id', 'order_id']
    search_fields = ['recipient', 'subject', 'correlation_id']
    ordering_fields = ['created_at', 'sent_at', 'status']

    @action(detail=False, methods=['post'], url_path='send')
    def send(self, request):
        """Primary integration endpoint for upstream services."""
        serializer = SendNotificationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        notifications_received_total.labels(type=data['type']).inc()
        correlation_id = getattr(request, 'correlation_id', '')

        notification = create_and_dispatch(
            user_id=data['user_id'],
            order_id=data.get('order_id'),
            event_id=data.get('event_id'),
            type=data['type'],
            channel=data['channel'],
            recipient=data['recipient'],
            subject=data.get('subject'),
            payload=data.get('payload', {}),
            correlation_id=correlation_id,
        )
        out = NotificationSerializer(notification).data
        return Response(out, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='retry')
    def retry(self, request, pk=None):
        notification = self.get_object()
        if notification.status == Notification.Status.SENT:
            return Response(
                {'detail': 'Notification already sent.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        dispatch(notification)
        return Response(NotificationSerializer(notification).data)

    @action(detail=False, methods=['get'], url_path='by_user')
    def by_user(self, request):
        user_id = request.query_params.get('user_id')
        if not user_id:
            return Response(
                {'detail': 'user_id query parameter is required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        qs = self.get_queryset().filter(user_id=user_id)
        page = self.paginate_queryset(qs)
        serializer = self.get_serializer(page or qs, many=True)
        if page is not None:
            return self.get_paginated_response(serializer.data)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        qs = self.get_queryset()
        by_status = dict(qs.values_list('status').annotate(c=Count('notification_id')))
        by_type = dict(qs.values_list('type').annotate(c=Count('notification_id')))
        by_channel = dict(qs.values_list('channel').annotate(c=Count('notification_id')))
        return Response({
            'total': qs.count(),
            'by_status': by_status,
            'by_type': by_type,
            'by_channel': by_channel,
        })
