from __future__ import print_function
import pickle
import os.path
import sys
from datetime import datetime, timezone, timedelta
from googleapiclient.discovery import build
from google_auth_oauthlib.flow import InstalledAppFlow, Flow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from urllib.parse import urlparse, parse_qs, ParseResult
from typing import Any, Dict, List

# If modifying these scopes, delete the file token.pickle.
SCOPES = ['https://www.googleapis.com/auth/calendar.readonly']
ZOOM_DOMAIN = "ellevationeducation"
NUM_NEXT = 5
# Skip the first meeting and join the second if it starts within this many minutes of now
SKIP_FIRST_IF_NEXT_STARTS_WITHIN = 3

def _fetch_creds() -> Credentials:
    """Attempts to load credentials from a pickle otherwise logs you in to get a token"""
    creds = None
    # The file token.pickle stores the user's access and refresh tokens, and is
    # created automatically when the authorization flow completes for the first
    # time.
    if os.path.exists('token.pickle'):
        with open('token.pickle', 'rb') as token:
            creds = pickle.load(token)
    # If there are no (valid) credentials available, let the user log in.
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow: InstalledAppFlow = InstalledAppFlow.from_client_secrets_file(
                'credentials.json', SCOPES)
            creds: Credentials = flow.run_local_server(port=0)
        # Save the credentials for the next run
        with open('token.pickle', 'wb') as token:
            pickle.dump(creds, token)

    return creds


def is_day_only(event: dict) -> bool:
    """Returns whether this event is an all-day event using the fact that start has date
    versus dateTime attributes"""
    return "date" in event["start"]


def is_not_day_only(event: dict) -> bool:
    return not is_day_only(event)


def get_zoom_link(event: dict) -> str:
    """Return the zoom link from the event data if it exists"""
    # First let's look in the location
    loc = event.get("location", "")
    if "zoom.us" in loc:
        # If the meeting is setup as zoom as a location, then it may have multiple.
        # Split as csv and find the first with zoom.us in it.
        if "," in loc:
            loc = next(l for l in loc.split(",") if "zoom.us" in l)
        return loc
    
    eps = event.get("conferenceData", {}).get("entryPoints", [])
    # Sometimes an event returns an empty array here which results in a StopIteration
    # error when we try to use the following for loop
    if eps:
        found = next(ep for ep in eps if "zoom.us" in ep.get("uri", ""))
        if found:
            return found["uri"]
        else:
            print("\tConference data found, but no zoom links in it")
    else:
        print("\tNo conference data found for event")
        # print(event)

    return None


def has_zoom_link(event: dict) -> bool:
    return get_zoom_link(event) is not None


def convert_to_zoom_protocol(url: str) -> str:
    """Take the incoming url and convert it to a zoom protocol url

    Convert this:
      https://ellevationeducation.zoom.us/j/1234?pwd=abcd
    to this
      zoommtg://ellevationeducation.zoom.us/join?action=join&confno=1234&pwd=abcd
    """
    parsed: ParseResult = urlparse(url)
    confno: str = parsed.path.split("/")[-1]
    qargs: Dict[str, List[str]] = parse_qs(parsed.query)

    zoom_url = [
        f"zoommtg://{ZOOM_DOMAIN}.zoom.us/join?action=join&confno=",
        confno
    ]
    if "pwd" in qargs:
        zoom_url.extend([
            "&pwd=",
            qargs["pwd"][0]
        ])

    return "".join(zoom_url)


def find_event_to_join(now: datetime, events: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Find the event to join"""
    first = events[0]
    if len(events) > 1:
        second = events[1]
        start = second['start'].get('dateTime', second['start'].get('date'))
        time = datetime.fromisoformat(start)
        delta = time - now
        if delta < timedelta(minutes=SKIP_FIRST_IF_NEXT_STARTS_WITHIN):
            print(f"Second event starts in {delta.min} minutes so joining that one")
            first = second

    return first


def main():
    """Shows basic usage of the Google Calendar API.
    Prints the start and name of the next 10 events on the user's calendar.
    """

    creds = _fetch_creds()
    service = build('calendar', 'v3', credentials=creds)

    # Call the Calendar API
    now: datetime = datetime.now(tz=timezone.utc)
    # now: datetime = datetime.now(tz=timezone.utc) - timedelta(hours=1)
    now_str: str = now.isoformat()
    print(f"Getting the upcoming {NUM_NEXT} events from {now_str}")
    events_result = service.events().list(calendarId='primary', timeMin=now_str,
                                        maxResults=NUM_NEXT, singleEvents=True,
                                        orderBy='startTime').execute()
    events = events_result.get('items', [])
    for event in events:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event["summary"]
        is_not_day = is_not_day_only(event)
        has_zoom = False
        if is_not_day:
            has_zoom = has_zoom_link(event)
        print(start, summary, is_not_day, has_zoom)

    if not events:
        print('No upcoming events found.')
    filtered = list(filter(has_zoom_link, filter(is_not_day_only, events)))
    # Debugging purposes...
    for event in filtered:
        start = event['start'].get('dateTime', event['start'].get('date'))
        summary = event["summary"]
        link = get_zoom_link(event)
        zl = convert_to_zoom_protocol(link)
        print(start, summary, zl)

    if filtered:
        e = find_event_to_join(now, filtered)
        if e:
            print()
            print("Joining zoom for")
            summary = e["summary"]
            zl = convert_to_zoom_protocol(get_zoom_link(e))
            print(summary, zl)
            cmd = f"open \"{zl}\""
            print(f"\t{cmd}")
            os.system(cmd)
        else:
            print()
            print("Of the zoom meetings found, unable to find one to join.")
    else:
        print()
        print("None of the upcoming meetings have zoom links.")


if __name__ == '__main__':
    main()