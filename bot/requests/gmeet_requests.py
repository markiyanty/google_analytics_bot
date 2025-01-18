import datetime
from googleapiclient.discovery import build
import config.auth as auth
import datetime, json
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import delete
from bot.database.models import GoogleMeetGuest, async_session
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build


def create_google_meet_link(credentials_json):
    # If credentials_json is a string, parse it into a dictionary
    if isinstance(credentials_json, str):
        credentials_info = json.loads(credentials_json)
    else:
        credentials_info = credentials_json

    # Create Credentials object
    credentials = Credentials.from_authorized_user_info(credentials_info, 'https://www.googleapis.com/auth/calendar')

    # Build the Calendar API service
    service = build('calendar', 'v3', credentials=credentials)

    # Define the Google Calendar event with a Meet link
    event = {
        'summary': 'Generated Google Meet',
        'start': {
            'dateTime': '2025-01-04T10:00:00+02:00',
            'timeZone': 'Europe/Kyiv',
        },
        'end': {
            'dateTime': '2025-01-04T11:00:00+02:00',
            'timeZone': 'Europe/Kyiv',
        },
        'conferenceData': {
            'createRequest': {
                'requestId': 'unique-request-id',
                'conferenceSolutionKey': {'type': 'hangoutsMeet'},
            },
        },
    }

    created_event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()

    return created_event['conferenceData']['entryPoints'][0]['uri']


async def schedule_google_meet(credentials_json, name, date, time, guests):
    if isinstance(credentials_json, str):
        credentials_info = json.loads(credentials_json)
    else:
        credentials_info = credentials_json

    # Get authenticated credentials
    credentials = Credentials.from_authorized_user_info(credentials_info, 'https://www.googleapis.com/auth/calendar')

    service = build('calendar', 'v3', credentials=credentials)

    # Parse start and end times
    event_start = datetime.datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    event_end = event_start + datetime.timedelta(hours=1)  # Default meeting duration: 1 hour

    # Create event payload
    event = {
        'summary': name,
        'description': 'A Google Meet meeting created via API.',
        'start': {
            'dateTime': event_start.isoformat(),
            'timeZone': 'Europe/Kiev',
        },
        'end': {
            'dateTime': event_end.isoformat(),
            'timeZone': 'Europe/Kiev',
        },
        'attendees': [{'email': guest.email} for guest in guests],  # Access `guest.email` directly
        'conferenceData': {
            'createRequest': {
                'conferenceSolutionKey': {
                    'type': 'hangoutsMeet'
                },
                'requestId': 'unique-request-id'  # A unique identifier for the request
            }
        },
    }

    # Insert the event and fetch the response
    created_event = service.events().insert(
        calendarId='primary',
        body=event,
        conferenceDataVersion=1
    ).execute()

    # Extract and return the Google Meet link
    meet_link = created_event.get('hangoutLink')
    print(f'Google Meet link: {meet_link}')
    return meet_link

# Add a guest to the database
async def add_guest(name, email):
    """Adds a new guest to the database."""
    async with async_session() as session:
        guest = GoogleMeetGuest(name=name, email=email)
        session.add(guest)
        try:
            await session.commit()
        except Exception as e:
            await session.rollback()  # Rollback in case of error
            raise e

# Delete a guest from the database
async def delete_guest(guest_id):
    async with async_session() as session:
        stmt = delete(GoogleMeetGuest).where(GoogleMeetGuest.id == guest_id)
        await session.execute(stmt)
        await session.commit()

# Fetch all guests
async def get_all_guests():
    async with async_session() as session:
        stmt = select(GoogleMeetGuest)
        result = await session.execute(stmt)
        return result.scalars().all()

