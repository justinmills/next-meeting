import json
from datetime import datetime
from typing import Dict

from next_meeting.parsing import MyEvent


def sample_my_event() -> MyEvent:
    return MyEvent(
        id="77gcalEventId_20210712T133000Z",
        start=datetime.fromisoformat("2021-07-12T09:30:00-04:00"),
        summary="JIRA Board Review",
        is_not_day_event=True,
        in_progress=False,
        is_next_joinable=False,
        zoom_link="zoommtg://example.zoom.us/join?action=join&confno=12345678987&pwd=SUPERSECRET1234",  # noqa: E501
        icon="icon.png",
    )


def read_event_file(file: str) -> Dict[str, str]:
    """Read one of the json files in tests/events/

    These may be raw response payloads from google or subsets for testing
    various bits"""
    with open(f"tests/events/{file}.json") as f:
        s = f.read()
        return json.loads(s)


def single_raw_event() -> Dict[str, str]:
    """Reads an event file from disk

    This one has zoom location data in all of the potential places we look for it.
    Specialized methods follow that will trim out selective pieces.
    """
    return read_event_file("single-event-all-3")
