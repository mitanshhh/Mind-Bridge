#Setup Twilio calling API

from twilio.rest import Client
from config.config import TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN, TWILIO_FROM_NUMBER, EMERGENCY_CONTACT
def call_emergency():
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        to = EMERGENCY_CONTACT,
        from_ = TWILIO_FROM_NUMBER,
        url = "http://demo.twilio.com/docs/voice.xml"
    )
    