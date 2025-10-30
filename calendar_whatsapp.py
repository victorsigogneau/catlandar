from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account
from twilio.rest import Client
import os

# --- Fuseau horaire Paris ---
PARIS = timezone(timedelta(hours=2))  # UTC+2 pour l'heure d'été/hiver

# --- Google Calendar ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

# Plage du jour en date
today = datetime.now(PARIS).date()
tomorrow = today + timedelta(days=1)

# Calendriers
calendar_ids = [
    'victor.sigogneau19@gmail.com',
    'catlandar@catlendar-476720.iam.gserviceaccount.com'
]

all_events = []

for cal_id in calendar_ids:
    events_result = service.events().list(
        calendarId=cal_id,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    for event in events_result.get('items', []):
        # Récupérer la date de début et de fin
        if 'dateTime' in event['start']:
            start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00')).astimezone(PARIS)
            end_dt = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')).astimezone(PARIS)
            if start_dt.date() == today:
                all_events.append((start_dt, event))
        else:
            # All-day event
            start_dt = datetime.fromisoformat(event['start']['date']).date()
            end_dt = datetime.fromisoformat(event['end']['date']).date()
            if start_dt <= today < end_dt:
                all_events.append((datetime.combine(today, datetime.min.time()), event))

# Trier tous les événements
all_events.sort(key=lambda x: x[0])

# --- Formater le message ---
if not all_events:
    message_body = "📅 Aucun événement prévu aujourd'hui."
else:
    message_body = "🗓️ Événements du jour :\n"
    for dt, event in all_events:
        if 'dateTime' in event['start']:
            start_time = dt.strftime('%H:%M')
        else:
            start_time = "Toute la journée"
        message_body += f"- {start_time} ({event.get('summary', '(sans titre)')})\n"

# --- Twilio WhatsApp ---
account_sid = os.getenv('TWILIO_SID')
auth_token = os.getenv('TWILIO_TOKEN')
to_number = os.getenv('TO_WHATSAPP')
from_number = 'whatsapp:+14155238886'

client = Client(account_sid, auth_token)
message = client.messages.create(
    from_=from_number,
    to=to_number,
    body=message_body
)

print("✅ Message WhatsApp envoyé :", message.sid)
