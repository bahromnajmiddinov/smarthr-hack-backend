from celery import shared_task
from django.conf import settings
from twilio.rest import Client


@shared_task
def send_verification_sms(phone, code):
    """Send SMS verification code using Twilio"""
    
    try:
        client = Client(
            settings.TWILIO_ACCOUNT_SID,
            settings.TWILIO_AUTH_TOKEN
        )
        
        message = client.messages.create(
            body=f'Your SmartHR verification code is: {code}',
            from_=settings.TWILIO_PHONE_NUMBER,
            to=phone
        )
        
        return {'success': True, 'sid': message.sid}
        
    except Exception as e:
        return {'success': False, 'error': str(e)}
    