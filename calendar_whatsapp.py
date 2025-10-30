from datetime import datetime, timedelta, timezone
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

# --- Fuseau horaire Paris ---
PARIS = timezone(timedelta(hours=2))

# Aujourd'hui
today = datetime.now(PARIS).date()

# --- Liste complète des IDs de calendriers ---
calendar_ids = [
    'victor.sigogneau19@gmail.com',
    '14728600221a78af9a60d5b407c7b628f226c7eb9415c1d6a58d0929d53d9e87@group.calendar.google.com',
    'a21c0adb47b981922cb499d89435c5ad1b9edca811e09dd8f543d3eef00794d5@group.calendar.google.com',
    '9f0248fcc657840b4ca77709eee8bd3f860334f79ae587c839bf830f0ad38170@group.calendar.google.com',
    '2cd905ae0f6e225a595d1b06b13b6902a3afc91fbe489265cc00ba066fac219a@group.calendar.google.com',
    '1957d73f2419f757b75b2d3c190b271deb4cd7c0824023a0a1716369352379cf@group.calendar.google.com',
    'ece46e97d1561024e460d5343310343769d2152f0ed6217c67be20f0698110f9@group.calendar.google.com',
    '7b1a7fe70fcd4175525a4a0ed3ac56d2ecb5d90e57106d16c32ead7cfe0ec2a0@group.calendar.google.com'
]

all_events = []

# --- Vérifier les calendriers accessibles ---
calendar_list = service.calendarList().list().execute()
print("Calendriers accessibles :")
for cal in calendar_list['items']:
    print(cal['summary'], "→", cal['id'])

# --- Récupérer les événements ---
for cal_id in calendar_ids:
    events_result = service.events().list(
        calendarId=cal_id,
        singleEvents=True,
        orderBy='startTime'
    ).execute()
    
    for event in events_result.get('items', []):
        print('event', event)
        
        # Événements horaires
        if 'dateTime' in event['start']:
            start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00')).astimezone(PARIS)
            end_dt = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')).astimezone(PARIS)
            if start_dt.date() == today:
                all_events.append((start_dt, event))
        else:
            # Événements "toute la journée"
            start_dt = datetime.combine(datetime.fromisoformat(event['start']['date']).date(), datetime.min.time(), tzinfo=PARIS)
            end_dt = datetime.combine(datetime.fromisoformat(event['end']['date']).date(), datetime.min.time(), tzinfo=PARIS)
            if start_dt.date() <= today < end_dt.date():
                all_events.append((start_dt, event))

# --- Trier tous les événements ---
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
from_number = 'whatsapp:+14155238886'  # Twilio sandbox

client = Client(account_sid, auth_token)
message = client.messages.create(
    from_=from_number,
    to=to_number,
    body=message_body
)

print("✅ Message WhatsApp envoyé :", message.sid)
