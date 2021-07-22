import textwrap
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from urllib.parse import ParseResult, parse_qs, urlparse

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
    zoom_link: Optional[str] = None
    icon: Optional[str] = None

    def to_item(self) -> Item:
        """Convert this to an Alfred Item for serialization"""
        return Item(
            uid=self.id,
            title=self.summary,
            subtitle=f"Starting at {self.start}",
            arg=self.zoom_link,
            variables=dict(
                title=self.summary,
                start=self.start,
            ),
            icon=(ItemIcon(path=self.icon) if self.icon else None),
        )


def get_zoom_link(event: Dict[str, str], args: Args) -> Optional[str]:
    """Return the zoom link from the event data if it exists"""
    # First let's look in the location
    loc = event.get("location", "")
    if "zoom.us" in loc:
        # If the meeting is setup as zoom as a location, then it may have multiple.
        # Split as csv and find the first with zoom.us in it.
        if "," in loc:
            loc = next(l for l in loc.split(",") if "zoom.us" in l)  # noqa: E741
        return loc

    eps = event.get("conferenceData", {}).get("entryPoints", [])
    # Sometimes an event returns an empty array here which results in a StopIteration
    # error when we try to use the following for loop
    if eps:
        found = next(ep for ep in eps if "zoom.us" in ep.get("uri", ""))
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

    return None


def convert_to_zoom_protocol(url: str) -> str:
    """Take the incoming url and convert it to a zoom protocol url

    Convert this:
      https://example.zoom.us/j/1234?pwd=abcd
    to this
      zoommtg://example.zoom.us/join?action=join&confno=1234&pwd=abcd
    """
    parsed: ParseResult = urlparse(url)
    hostname: str = parsed.hostname
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

    link = get_zoom_link(event, args)
    zoom_link = None
    if link:
        zoom_link = convert_to_zoom_protocol(link)

    icon = None
    if "1:1" in summary:
        icon = "one.png"
    elif "Standup" in summary:
        icon = "standup.png"
    else:
        icon = "icon.png"

    return MyEvent(
        id=id,
        start=start,
        summary=summary,
        is_not_day_event=is_not_day,
        zoom_link=zoom_link,
        in_progress=in_progress,
        is_next_joinable=is_next_joinable,
        icon=icon,
    )


def parse_events(events: List[Dict[str, str]], args: Args) -> List[MyEvent]:
    """Converts a Google calendar event (dict) into a MyEvent"""

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
          Markers: {event.is_not_day_event} | {event.in_progress} | {event.is_next_joinable}  # noqa: E501
          Link   : {event.zoom_link}"""
        _debug(textwrap.dedent(event_string), format)
