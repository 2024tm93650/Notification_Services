"""Notification model — stores every notification dispatched by the service.

Note: user_id, order_id, event_id are stored as plain integers (no FK).
Cross-service foreign keys are intentionally avoided to keep this service's
database fully independent (database-per-service principle).
"""
from django.db import models


class Notification(models.Model):
    class Type(models.TextChoices):
        ORDER_CONFIRMED = 'ORDER_CONFIRMED', 'Order Confirmed'
        ORDER_CANCELLED = 'ORDER_CANCELLED', 'Order Cancelled'
        PAYMENT_FAILED = 'PAYMENT_FAILED', 'Payment Failed'
        PAYMENT_REFUNDED = 'PAYMENT_REFUNDED', 'Payment Refunded'
        EVENT_CANCELLED = 'EVENT_CANCELLED', 'Event Cancelled'
        SEAT_RESERVED = 'SEAT_RESERVED', 'Seat Reserved'
        WELCOME = 'WELCOME', 'Welcome'

    class Channel(models.TextChoices):
        EMAIL = 'EMAIL', 'Email'
        SMS = 'SMS', 'SMS'

    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        SENT = 'SENT', 'Sent'
        FAILED = 'FAILED', 'Failed'

    notification_id = models.AutoField(primary_key=True)
    user_id = models.IntegerField(db_index=True)
    order_id = models.IntegerField(null=True, blank=True, db_index=True)
    event_id = models.IntegerField(null=True, blank=True)

    type = models.CharField(max_length=32, choices=Type.choices)
    channel = models.CharField(max_length=16, choices=Channel.choices, default=Channel.EMAIL)
    recipient = models.CharField(max_length=255)
    subject = models.CharField(max_length=255, blank=True)
    message = models.TextField()

    status = models.CharField(
        max_length=16, choices=Status.choices, default=Status.PENDING, db_index=True,
    )
    retry_count = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)

    correlation_id = models.CharField(max_length=64, blank=True, db_index=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    sent_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user_id', 'status']),
            models.Index(fields=['type', 'status']),
        ]

    def __str__(self):
        return f'#{self.notification_id} [{self.type}] -> {self.recipient} ({self.status})'
