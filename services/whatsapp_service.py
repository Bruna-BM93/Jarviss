from twilio.rest import Client
import os

ACCOUNT_SID = os.environ.get('TWILIO_ACCOUNT_SID')
AUTH_TOKEN = os.environ.get('TWILIO_AUTH_TOKEN')
TWILIO_WHATSAPP_NUMBER = os.environ.get('TWILIO_WHATSAPP_NUMBER')

client = Client(ACCOUNT_SID, AUTH_TOKEN)

def send_whatsapp_message(to, body):
    try:
        message = client.messages.create(
            from_=f'whatsapp:{TWILIO_WHATSAPP_NUMBER}',
            body=body,
            to=f'whatsapp:{to}'
        )
        return message.sid
    except Exception as e:
        return str(e)
