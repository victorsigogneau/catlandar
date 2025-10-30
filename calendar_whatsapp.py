from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account
from twilio.rest import Client
import os

# --- Fuseau horaire Paris ---
PARIS = timezone(timedelta(hours=2))  # UTC+2 pour l'heure d'été/hiver, ajuster si besoin

# --- Google Calendar ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

# Plage horaire : aujourd'hui Paris
now = datetime.now(PARIS).isoformat()
end_of_day = (datetime.now(PARIS) + timedelta(days=1)).isoformat()

# --- Récupération de tous les calendriers accessibles ---
calendar_list = service.calendarList().list().execute()
calendar_ids = [cal['id'] for cal in calendar_list['items']]

all_events = []

for cal_id in calendar_ids:
    events_result = service.events().list(
        calendarId=cal_id,
        timeMin=now,
        timeMax=end_of_day,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    all_events.extend(events_result.get('items', []))

# Trier tous les événements par heure (ou date pour all-day)
def get_start_time(event):
    if 'dateTime' in event['start']:
        return datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
    else:
        return datetime.fromisoformat(event['start']['date'])

all_events.sort(key=get_start_time)

# --- Formater le message ---
if not all_events:
    message_body = "📅 Aucun événement prévu aujourd'hui."
else:
    message_body = "🗓️ Événements du jour :\n"
    for event in all_events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        if 'dateTime' in event['start']:
            start_time = datetime.fromisoformat(start.replace('Z', '+00:00')).astimezone(PARIS).strftime('%H:%M')
        else:
            start_time = "Toute la journée"
        message_body += f"- {start_time} ({event.get('summary', '(sans titre)')})\n"

# --- Twilio WhatsApp ---
account_sid = os.getenv('TWILIO_SID')
auth_token = os.getenv('TWILIO_TOKEN')
to_number = os.getenv('TO_WHATSAPP')
from_number = 'whatsapp:+14155238886'  # Twilio sandbox

client = Client(account_sid, auth_token)

message = client.messages.create(
    from_=from_number,
    to=to_number,
    body=message_body
)

print("✅ Message WhatsApp envoyé :", message.sid)
