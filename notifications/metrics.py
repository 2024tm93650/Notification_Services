"""Prometheus metrics for the notification service."""
from prometheus_client import Counter

notifications_sent_total = Counter(
    'notifications_sent_total',
    'Total notifications successfully sent',
    ['type', 'channel'],
)

notifications_failed_total = Counter(
    'notifications_failed_total',
    'Total notifications that failed to send',
    ['type', 'channel', 'reason'],
)

notifications_received_total = Counter(
    'notifications_received_total',
    'Total notification requests received from upstream services',
    ['type'],
)
