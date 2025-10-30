from datetime import datetime, timedelta, timezone
from googleapiclient.discovery import build
from google.oauth2 import service_account

# --- Fuseau horaire Paris ---
PARIS = timezone(timedelta(hours=2))  # UTC+2, ajuste si nécessaire

# --- Google Calendar ---
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
SERVICE_ACCOUNT_FILE = 'service-account.json'

creds = service_account.Credentials.from_service_account_file(
    SERVICE_ACCOUNT_FILE, scopes=SCOPES)
service = build('calendar', 'v3', credentials=creds)

# Aujourd'hui en date
today = datetime.now(PARIS).date()

# Calendriers à récupérer
calendar_ids = [
    'victor.sigogneau19@gmail.com',                      # calendrier principal
    'catlandar@catlendar-476720.iam.gserviceaccount.com' # calendrier partagé
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

# Trier tous les événements par date/heure
all_events.sort(key=lambda x: x[0])

# --- Affichage pour debug ---
if not all_events:
    print("📅 Aucun événement prévu aujourd'hui.")
else:
    print("🗓️ Événements du jour :")
    for dt, event in all_events:
        if 'dateTime' in event['start']:
            start_time = dt.strftime('%H:%M')
        else:
            start_time = "Toute la journée"
        calendar_name = event.get('organizer', {}).get('email', 'Calendrier inconnu')
        print(f"- {start_time} ({event.get('summary', '(sans titre)')}) | {calendar_name}")
