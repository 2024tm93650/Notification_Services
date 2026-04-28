from django.contrib import admin
from .models import Notification


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = (
        'notification_id', 'type', 'channel', 'recipient',
        'status', 'user_id', 'order_id', 'created_at', 'sent_at',
    )
    list_filter = ('status', 'type', 'channel')
    search_fields = ('recipient', 'subject', 'correlation_id')
    readonly_fields = ('created_at', 'updated_at', 'sent_at')
