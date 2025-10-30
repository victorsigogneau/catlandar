from datetime import datetime, timedelta
from googleapiclient.discovery import build
from google.oauth2 import service_account
from twilio.rest import Client
import os

# --- Google Calendar ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

now = datetime.utcnow().isoformat() + 'Z'
end_of_day = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'

events_result = service.events().list(
    calendarId='primary', timeMin=now, timeMax=end_of_day,
    singleEvents=True, orderBy='startTime').execute()
events = events_result.get('items', [])

if not events:
    message_body = "📅 Aucun événement prévu aujourd'hui."
else:
    message_body = "🗓️ Événements du jour :\n"
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        start_time = datetime.fromisoformat(start.replace('Z', '+00:00')).strftime('%H:%M')
        message_body += f"- {start_time} : {event.get('summary', '(sans titre)')}\n"

# --- Twilio WhatsApp ---
account_sid = os.getenv('TWILIO_SID')
auth_token = os.getenv('TWILIO_TOKEN')
to_number = os.getenv('TO_WHATSAPP')
from_number = 'whatsapp:+14155238886'  # numéro Twilio Sandbox

client = Client(account_sid, auth_token)

message = client.messages.create(
    from_=from_number,
    to=to_number,
    body=message_body
)

print("✅ Message WhatsApp envoyé :", message.sid)
