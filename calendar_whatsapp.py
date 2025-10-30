from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account
from twilio.rest import Client
import os

PARIS = timezone(timedelta(hours=2))  # UTC+2

SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

today = datetime.now(PARIS).date()

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
        if 'dateTime' in event['start']:
            start_dt = datetime.fromisoformat(event['start']['dateTime'].replace('Z', '+00:00')).astimezone(PARIS)
            end_dt = datetime.fromisoformat(event['end']['dateTime'].replace('Z', '+00:00')).astimezone(PARIS)
            if start_dt.date() == today:
                all_events.append((start_dt, event))
        else:
            # All-day event → transforme en offset-aware en 00:00 Paris
            start_dt = datetime.combine(datetime.fromisoformat(event['start']['date']).date(), datetime.min.time(), tzinfo=PARIS)
            end_dt = datetime.combine(datetime.fromisoformat(event['end']['date']).date(), datetime.min.time(), tzinfo=PARIS)
            if start_dt.date() <= today < end_dt.date():
                all_events.append((start_dt, event))

# Trier maintenant tous les datetime offset-aware
all_events.sort(key=lambda x: x[0])

# --- Affichage debug ---
if not all_events:
    print("📅 Aucun événement prévu aujourd'hui.")
else:
    print("🗓️ Événements du jour :")
    for dt, event in all_events:
        if 'dateTime' in event['start']:
            start_time = dt.strftime('%H:%M')
        else:
            start_time = "Toute la journée"
        print(f"- {start_time} ({event.get('summary', '(sans titre)')})")
