"""Plain-text templates for each notification type. Kept simple/inline so the
service has zero template-engine dependencies for content rendering."""
from ..models import Notification


def _fmt_seats(payload):
    seats = payload.get('seats') or []
    return ', '.join(str(s) for s in seats) if seats else 'N/A'


def build_subject_and_body(notification_type: str, payload: dict) -> tuple[str, str]:
    event = payload.get('event_name', 'your event')
    venue = payload.get('venue', '')
    when = payload.get('event_date', '')
    total = payload.get('total', '')
    order_id = payload.get('order_id', '')
    seats = _fmt_seats(payload)

    if notification_type == Notification.Type.ORDER_CONFIRMED:
        subject = f'Booking Confirmed: {event}'
        body = (
            f'Hi,\n\nYour booking for {event} is confirmed.\n'
            f'Venue: {venue}\nDate: {when}\nSeats: {seats}\n'
            f'Order: #{order_id}\nTotal Paid: {total}\n\n'
            f'Show this email at the venue. Enjoy the show!\n'
        )
    elif notification_type == Notification.Type.ORDER_CANCELLED:
        subject = f'Booking Cancelled: {event}'
        body = (
            f'Your booking #{order_id} for {event} has been cancelled.\n'
            f'Any payment will be refunded within 5-7 business days.\n'
        )
    elif notification_type == Notification.Type.PAYMENT_FAILED:
        subject = 'Payment Failed'
        body = (
            f'Payment for order #{order_id} could not be processed.\n'
            f'Reserved seats have been released. Please try again.\n'
        )
    elif notification_type == Notification.Type.PAYMENT_REFUNDED:
        subject = 'Refund Processed'
        body = (
            f'A refund of {total} has been initiated for order #{order_id}.\n'
            f'It will reflect in your account within 5-7 business days.\n'
        )
    elif notification_type == Notification.Type.EVENT_CANCELLED:
        subject = f'Event Cancelled: {event}'
        body = (
            f'We regret to inform you that {event} on {when} has been cancelled.\n'
            f'A full refund for order #{order_id} will be processed automatically.\n'
        )
    elif notification_type == Notification.Type.SEAT_RESERVED:
        subject = 'Seats Held — Complete Your Payment'
        body = (
            f'Seats {seats} for {event} are held for 15 minutes.\n'
            f'Please complete payment for order #{order_id} to confirm.\n'
        )
    elif notification_type == Notification.Type.WELCOME:
        subject = 'Welcome to the Event Ticketing Platform'
        body = 'Thanks for signing up. Browse upcoming events and book your seats today.\n'
    else:
        subject = 'Notification'
        body = str(payload)

    return subject, body
