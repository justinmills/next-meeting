import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import ParseResult, parse_qs, urlparse

from bs4 import BeautifulSoup

from . import constants as c
from .alfred import Item, ItemIcon
from .args import Args, OutputFormat, _debug


@dataclass
class MyEvent:
    """
    Our version of a GCal event

    ...with stronger types and some logical attributes about the event exposed
    """

    id: str
    start: Optional[datetime]
    summary: str
    is_not_day_event: bool = True
    # Is the current meeting in progress
    in_progress: bool = False
    # Does this event start within a "joinable" time frame?
    is_next_joinable: bool = False
    meeting_link: Optional[str] = None
    icon: Optional[str] = None

    def to_item(self) -> Item:
        """Convert this to an Alfred Item for serialization"""
        return Item(
            uid=self.id,
            title=self.summary,
            subtitle=f"Starting at {self.start}",
            arg=self.meeting_link,
            variables=dict(
                title=self.summary,
                start=self.start,
            ),
            icon=(ItemIcon(path=self.icon) if self.icon else None),
        )


def is_zoom_link(value: str) -> bool:
    return "zoom.us" in value


def is_google_meet_link(value: str) -> bool:
    return "meet.google.com" in value


def has_meeting_link(value: str) -> bool:
    """Given a string (presumably a url), parse the meeting link out of it

    NOTE: this is the link used to join the meeting, so it's a URI in as native
    a format as possible (zoom links for zoom meetings, not http links)"""
    if is_zoom_link(value):
        return True
    elif is_google_meet_link(value):
        return True
    return False


def get_meeting_link(event: Dict[str, str], args: Args) -> Optional[str]:
    """Given a parsed GCal event return any found meeting link

    Order is:
    - location
    - conferenceData (conferenceData.entrypoints[].uri)
    - description

    Within each of these, we prefer zoom links over Google meet links (sorry
    Google).

    Reference: https://developers.google.com/calendar/api/v3/reference/events"""

    # Location - note this may be a csv of locations
    locations: List[str] = event.get("location", "").split(",")
    location: str | None = next(
        (location for location in locations if has_meeting_link(location)), None
    )
    if location:
        return str(location)

    # Conference Data - this is a list so we must check each element
    eps = event.get("conferenceData", {}).get("entryPoints", [])  # type: ignore
    if eps:
        found = next((ep for ep in eps if has_meeting_link(ep.get("uri", ""))), None)
        if found:
            return str(found["uri"])
        else:
            _debug(
                "Conference data found, but no zoom links in it for "
                + event["summary"],
                args.format,
            )
    else:
        _debug("No conference data found for " + event["summary"], args.format)

    # Description - any links (parsed as HTML)
    description: str = event.get("description", "--empty--")
    try:
        soup: BeautifulSoup = BeautifulSoup(description, "html.parser")
        for link in soup.find_all("a"):
            href = link.get("href")
            if has_meeting_link(href):
                return str(href)
        _debug(
            "No zoom links found in description for " + event["summary"], args.format
        )
    except Exception as e:
        _debug(f"Error parsing description: {e}", args.format)

    return None


def get_icon(summary: str) -> str:
    """Given some details about a meeting, return the icon we should use"""
    if "1:1" in summary:
        return "one.png"
    elif "Standup" in summary:
        return "standup.png"

    return "icon.png"


def convert_to_zoom_protocol(url: str) -> str:
    """Take the incoming url and convert it to a zoom protocol url

    Convert this:
      https://example.zoom.us/j/1234?pwd=abcd
    to this
      zoommtg://example.zoom.us/join?action=join&confno=1234&pwd=abcd

    This is so you can delegate to the OS to open a zoom meeting directly in the
    app instead of going through the browser to then open zoom.
    """
    parsed: ParseResult = urlparse(url)
    hostname: Optional[str] = parsed.hostname
    confno: str = parsed.path.split("/")[-1]
    qargs: Dict[str, List[str]] = parse_qs(parsed.query)

    zoom_url = [f"zoommtg://{hostname}/join?action=join&confno=", confno]
    if "pwd" in qargs:
        zoom_url.extend(["&pwd=", qargs["pwd"][0]])

    return "".join(zoom_url)


def parse_event_datetime(d: Dict[str, str]) -> Optional[datetime]:
    datetime_or_date = d.get("dateTime", d.get("date"))
    # TODO: deal with timezones...
    # timezone = d.get("timeZone")
    if datetime_or_date:
        try:
            return datetime.fromisoformat(datetime_or_date)
            # TODO: catch specific errors
        except:  # noqa: E722
            pass
    return None


def is_not_day_only(event: Dict[str, str]) -> bool:
    """Returns whether this event is a normal event or an all-day event using
    the fact that start has date versus a dateTime attribute"""
    return "date" not in event["start"]


def parse_event(event: Dict[str, Any], args: Args) -> MyEvent:
    """Parses a single GCal event"""
    id = event["id"]

    start = parse_event_datetime(event["start"])
    end = parse_event_datetime(event["end"])
    is_not_day = is_not_day_only(event)
    # If start/end are None this evaluates to None.
    in_progress = (
        is_not_day and start and end and start <= args.now and end >= args.now or False
    )
    is_next_joinable = False
    if is_not_day and not in_progress and start and start > args.now:
        delta = start - args.now
        is_next_joinable = delta < timedelta(minutes=c.JOINABLE_IF_NEXT_STARTS_WITHIN)

    summary = event["summary"]

    meeting_link: str | None = get_meeting_link(event, args)
    if meeting_link and is_zoom_link(meeting_link):
        # Convert from a https link to a zoom meeting (which will just open a
        # tab you have to close later, convert it to the native protocol to open
        # the app directly)
        meeting_link = convert_to_zoom_protocol(meeting_link)

    icon = get_icon(summary)

    return MyEvent(
        id=id,
        start=start,
        summary=summary,
        is_not_day_event=is_not_day,
        meeting_link=meeting_link,
        in_progress=in_progress,
        is_next_joinable=is_next_joinable,
        icon=icon,
    )


def parse_events(events: List[Dict[str, str]], args: Args) -> List[MyEvent]:
    """Converts a list of Google calendar events into a List of MyEvents

    Each GCal event is stored in a dict and each one will be converted to a
    MyEvent whether or not it has a meeting in it or not.
    """

    def augment(event: Dict[str, str]) -> MyEvent:
        return parse_event(event, args)

    return list(map(augment, events))


def _debug_event_list(events: List[MyEvent], format: OutputFormat) -> None:
    """Debug each event in a well formatted manner"""
    for event in events:
        event_string = f"""\
        Event: {event.id}
          Summary: {event.summary}
          Start  : {event.start}
          Markers: {event.is_not_day_event} | {event.in_progress} | {event.is_next_joinable}
          Link   : {event.meeting_link}"""  # noqa: E501
        _debug(textwrap.dedent(event_string), format)
