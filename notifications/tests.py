"""Basic tests for the notification service."""
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from .models import Notification


class NotificationModelTests(TestCase):
    def test_create_notification(self):
        n = Notification.objects.create(
            user_id=1, type=Notification.Type.WELCOME,
            channel=Notification.Channel.EMAIL,
            recipient='a@b.com', message='hi',
        )
        self.assertEqual(n.status, Notification.Status.PENDING)
        self.assertEqual(n.retry_count, 0)


class SendEndpointTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    @patch('notifications.services.senders.EmailSender.send')
    def test_send_order_confirmed(self, mock_send):
        payload = {
            'user_id': 42,
            'order_id': 101,
            'type': 'ORDER_CONFIRMED',
            'channel': 'EMAIL',
            'recipient': 'user@example.com',
            'payload': {
                'event_name': 'Coldplay', 'venue': 'Stadium',
                'seats': ['A1', 'A2'], 'total': 5250, 'order_id': 101,
            },
        }
        resp = self.client.post('/api/notifications/send/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['status'], 'SENT')
        mock_send.assert_called_once()

    @patch('notifications.services.senders.EmailSender.send', side_effect=RuntimeError('smtp down'))
    def test_send_marks_failed_on_error(self, _mock_send):
        payload = {
            'user_id': 1, 'type': 'WELCOME', 'channel': 'EMAIL',
            'recipient': 'a@b.com', 'payload': {},
        }
        resp = self.client.post('/api/notifications/send/', payload, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['status'], 'FAILED')
        self.assertIn('smtp down', resp.data['error_message'])


class HealthTests(TestCase):
    def test_health(self):
        resp = self.client.get('/health/')
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.json()['status'], 'ok')
