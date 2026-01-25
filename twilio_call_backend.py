#Setup Twilio calling API
import os
from dotenv import load_dotenv
from twilio.rest import Client
load_dotenv()

TWILIO_ACCOUNT_SID = os.getenv('TWILIO_ACCOUNT_SID')
TWILIO_AUTH_TOKEN = os.getenv('TWILIO_AUTH_TOKEN')
TWILIO_FROM_NUMBER = os.getenv('TWILIO_FROM_NUMBER')
EMERGENCY_CONTACT = os.getenv('EMERGENCY_CONTACT')


def call_emergency():
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    call = client.calls.create(
        to = EMERGENCY_CONTACT,
        from_ = TWILIO_FROM_NUMBER,
        url = "http://demo.twilio.com/docs/voice.xml"
    )
    