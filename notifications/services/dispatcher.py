"""Notification dispatcher — orchestrates building, persisting, and sending."""
import logging
from django.utils import timezone

from ..models import Notification
from ..metrics import notifications_sent_total, notifications_failed_total
from .senders import EmailSender, SmsSender
from .templates import build_subject_and_body

logger = logging.getLogger('notifications')

_CHANNEL_SENDERS = {
    Notification.Channel.EMAIL: EmailSender,
    Notification.Channel.SMS: SmsSender,
}


def dispatch(notification: Notification) -> Notification:
    """Send a persisted notification through its channel and update status."""
    sender = _CHANNEL_SENDERS.get(notification.channel)
    if sender is None:
        notification.status = Notification.Status.FAILED
        notification.error_message = f'Unsupported channel: {notification.channel}'
        notification.save(update_fields=['status', 'error_message', 'updated_at'])
        notifications_failed_total.labels(
            type=notification.type, channel=notification.channel, reason='unsupported_channel',
        ).inc()
        return notification

    try:
        sender.send(notification.recipient, notification.subject, notification.message)
        notification.status = Notification.Status.SENT
        notification.sent_at = timezone.now()
        notification.error_message = ''
        notification.save(update_fields=['status', 'sent_at', 'error_message', 'updated_at'])
        notifications_sent_total.labels(
            type=notification.type, channel=notification.channel,
        ).inc()
    except Exception as exc:  # noqa: BLE001 — we want to capture all transport errors
        notification.status = Notification.Status.FAILED
        notification.retry_count += 1
        notification.error_message = str(exc)[:1000]
        notification.save(update_fields=[
            'status', 'retry_count', 'error_message', 'updated_at',
        ])
        notifications_failed_total.labels(
            type=notification.type,
            channel=notification.channel,
            reason=type(exc).__name__,
        ).inc()
        logger.exception(f'Failed to send notification {notification.notification_id}')

    return notification


def create_and_dispatch(*, user_id, type, channel, recipient,
                        order_id=None, event_id=None, subject=None,
                        payload=None, correlation_id='') -> Notification:
    """Build subject/body from the payload, persist a row, then dispatch."""
    payload = payload or {}
    built_subject, body = build_subject_and_body(type, payload)
    notification = Notification.objects.create(
        user_id=user_id,
        order_id=order_id,
        event_id=event_id,
        type=type,
        channel=channel,
        recipient=recipient,
        subject=subject or built_subject,
        message=body,
        correlation_id=correlation_id,
    )
    return dispatch(notification)
