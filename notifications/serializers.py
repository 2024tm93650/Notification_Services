from rest_framework import serializers
from .models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'
        read_only_fields = (
            'notification_id', 'status', 'retry_count', 'error_message',
            'created_at', 'updated_at', 'sent_at',
        )


class SendNotificationSerializer(serializers.Serializer):
    """Payload other services POST to /api/notifications/send/."""
    user_id = serializers.IntegerField()
    order_id = serializers.IntegerField(required=False, allow_null=True)
    event_id = serializers.IntegerField(required=False, allow_null=True)
    type = serializers.ChoiceField(choices=Notification.Type.choices)
    channel = serializers.ChoiceField(
        choices=Notification.Channel.choices, default=Notification.Channel.EMAIL,
    )
    recipient = serializers.CharField(max_length=255)
    subject = serializers.CharField(max_length=255, required=False, allow_blank=True)
    payload = serializers.JSONField(required=False, default=dict)
