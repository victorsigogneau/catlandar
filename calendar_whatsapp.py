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

# Plage horaire : aujourd'hui UTC
now = datetime.utcnow().isoformat() + 'Z'
end_of_day = (datetime.utcnow() + timedelta(days=1)).isoformat() + 'Z'

# Liste des IDs de calendriers à récupérer
calendar_ids = [
    'victor.sigogneau19@gmail.com',                      # ton calendrier principal
    'catlandar@catlendar-476720.iam.gserviceaccount.com' # calendrier partagé
]

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

# Trier tous les événements par date/heure
def get_start(event):
    if 'dateTime' in event['start']:
        return datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00'))
    else:
        return datetime.fromisoformat(event['start']['date'])

all_events.sort(key=get_start)

# --- Formater le message ---
if not all_events:
    message_body = "📅 Aucun événement prévu aujourd'hui."
else:
    message_body = "🗓️ Événements du jour :\n"
    for event in all_events:
        if 'dateTime' in event['start']:
            start_time = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00')).strftime('%H:%M')
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
