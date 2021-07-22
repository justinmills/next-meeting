import json
import os.path
import pickle
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build

from . import constants as c
from .args import Args, _debug


def fetch_events(args: Args) -> List[Dict[str, str]]:
    creds = _fetch_creds()
    service = build("calendar", "v3", credentials=creds)

    # Call the Calendar API
    now: datetime = args.now
    time_min: str = now.isoformat()
    time_max: str = (now + timedelta(hours=c.HOURS_AHEAD)).isoformat()
    _debug(
        f"Getting the upcoming {c.NUM_NEXT} events from {time_min} to {time_max}",
        args.format,
    )
    events_result = (
        service.events()
        .list(
            calendarId="primary",
            timeMin=time_min,
            timeMax=time_max,
            maxResults=c.NUM_NEXT,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    if c.DEBUG_RAW_EVENTS:
        _debug("----------", args.format)
        _debug("Dumping raw results from google api", args.format)
        _debug(events_result, args.format)
        _debug("Again, in JSON", args.format)
        _debug(json.dumps(events_result), args.format)
        _debug("----------", args.format)
    events: List[Dict[str, str]] = events_result.get("items", [])
    return events


def _fetch_creds() -> Optional[Credentials]:
    """Attempts to load credentials from a pickle otherwise logs you in to get a
    token"""
    creds: Optional[Credentials] = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists("token.pickle"):
        with open("token.pickle", "rb") as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
                "credentials.json", c.SCOPES
            )
            creds = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open("token.pickle", "wb") as token:
            pickle.dump(creds, token)

    return creds
