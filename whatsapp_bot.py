import os
from typing import Optional
import requests

TWILIO_SID = os.environ.get('TWILIO_SID')
TWILIO_TOKEN = os.environ.get('TWILIO_TOKEN')
TWILIO_FROM = os.environ.get('TWILIO_FROM')
TWILIO_TO = os.environ.get('TWILIO_TO')


def send_message(text: str) -> Optional[str]:
    if not all([TWILIO_SID, TWILIO_TOKEN, TWILIO_FROM, TWILIO_TO]):
        print('Twilio credentials not configured')
        return None
    url = f'https://api.twilio.com/2010-04-01/Accounts/{TWILIO_SID}/Messages.json'
    data = {'From': TWILIO_FROM, 'To': TWILIO_TO, 'Body': text}
    try:
        resp = requests.post(url, data=data, auth=(TWILIO_SID, TWILIO_TOKEN))
        if resp.status_code == 201:
            return resp.json().get('sid')
        print('Twilio error', resp.text)
    except Exception as exc:
        print('Twilio exception', exc)
    return None
