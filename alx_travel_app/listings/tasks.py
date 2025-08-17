# listings/tasks.py

from celery import shared_task
from django.core.mail import send_mail
from django.conf import settings

from .models import Booking, Payment

@shared_task
def send_booking_confirmation_email(booking_id):
    """
    Celery task to send a booking confirmation email.
    """
    try:
        booking = Booking.objects.get(id=booking_id)
        subject = 'Booking Confirmed!'
        message = f"Hello {booking.guest.first_name},\n\nYour booking for {booking.listing.title} has been confirmed. We look forward to seeing you!\n\nDetails:\n- Check-in: {booking.start_date}\n- Check-out: {booking.end_date}\n- Total Price: {booking.total_price}\n\nThanks,\nYour Booking App Team"
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [booking.guest.email]

        send_mail(subject, message, from_email, recipient_list)
        print(f"Sent confirmation email for booking {booking_id}")
    except Booking.DoesNotExist:
        print(f"Booking {booking_id} not found. Cannot send email.")
    except Exception as e:
        print(f"Failed to send email for booking {booking_id}: {e}")
