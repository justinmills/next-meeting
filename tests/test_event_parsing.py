from datetime import datetime

import pytest
from next_meeting.args import Args
from next_meeting.parsing import MyEvent, parse_event, parse_events


def expected_event(id="12345678987") -> MyEvent:
    return MyEvent(
        id="77gcalEventId_20210712T133000Z",
        start=datetime.fromisoformat("2021-07-12T09:30:00-04:00"),
        summary="JIRA Board Review",
        is_not_day_event=True,
        in_progress=False,
        is_next_joinable=False,
        zoom_link=f"zoommtg://example.zoom.us/join?action=join&confno={id}&pwd=SUPERSECRET1234",  # noqa: E501
        icon="icon.png",
    )


@pytest.fixture
def expected_single_event() -> MyEvent:
    return expected_event()


@pytest.fixture
def expected_single_event_from_location() -> MyEvent:
    return expected_event("12345678987")


@pytest.fixture
def expected_single_event_from_conferenceData() -> MyEvent:
    return expected_event("22345678987")


@pytest.fixture
def expected_single_event_from_description() -> MyEvent:
    return expected_event("32345678987")


def test_parse_events(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    parsed_event = parse_event(single_raw_event, args)
    assert parsed_event == expected_single_event


def test_parse_event_in_progress(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    args.now = datetime.fromisoformat("2021-07-12T09:37:00-04:00")
    parsed_events = parse_events([single_raw_event], args)
    expected_single_event.in_progress = True
    assert len(parsed_events) == 1
    assert parsed_events[0] == expected_single_event


def test_parse_event_next_joinable(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    args.now = datetime.fromisoformat("2021-07-12T09:28:00-04:00")
    parsed_events = parse_events([single_raw_event], args)
    expected_single_event.is_next_joinable = True
    assert len(parsed_events) == 1
    assert parsed_events[0] == expected_single_event


def test_parse_event_no_zoom(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    single_raw_event["location"] = "!GooberZ!"
    del single_raw_event["conferenceData"]
    single_raw_event["description"] = "My Test Meeting"
    parsed_events = parse_events([single_raw_event], args)
    expected_single_event.zoom_link = None
    assert len(parsed_events) == 1
    assert parsed_events[0] == expected_single_event


def test_parse_event_multiple_locations(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    existing_location = single_raw_event["location"]
    single_raw_event["location"] = f"!GooberZ!,{existing_location}"
    parsed_event = parse_event(single_raw_event, args)
    assert parsed_event == expected_single_event


def test_parse_event_conferenceData(
    args: Args,
    single_raw_event_conferenceData_only: dict,
    expected_single_event_from_conferenceData: MyEvent,
):
    parsed_event = parse_event(single_raw_event_conferenceData_only, args)
    assert parsed_event == expected_single_event_from_conferenceData


def test_parse_event_conferenceData_no_zoom(
    args: Args,
    single_raw_event_conferenceData_only: dict,
    expected_single_event: MyEvent,
):
    single_raw_event_conferenceData_only["conferenceData"]["entryPoints"][0][
        "uri"
    ] = "https://www.google.com"
    parsed_event = parse_event(single_raw_event_conferenceData_only, args)
    expected_single_event.zoom_link = None
    assert parsed_event == expected_single_event


def test_parse_event_one_on_one(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    summary = "You and I 1:1!"
    single_raw_event["summary"] = summary
    parsed_events = parse_events([single_raw_event], args)
    expected_single_event.summary = summary
    expected_single_event.icon = "one.png"
    assert len(parsed_events) == 1
    assert parsed_events[0] == expected_single_event


def test_parse_event_standup(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    summary = "MyTeam Standup"
    single_raw_event["summary"] = summary
    parsed_events = parse_events([single_raw_event], args)
    expected_single_event.summary = summary
    expected_single_event.icon = "standup.png"
    assert len(parsed_events) == 1
    assert parsed_events[0] == expected_single_event


def test_parse_event_bad_time(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    single_raw_event["start"]["dateTime"] = "unparseable"
    parsed_events = parse_events([single_raw_event], args)
    expected_single_event.start = None
    expected_single_event.in_progress = False
    assert len(parsed_events) == 1
    assert parsed_events[0] == expected_single_event


def test_parse_event_all_day(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    single_raw_event["start"]["date"] = "2021-07-12"
    single_raw_event["end"]["date"] = "2021-07-12"
    del single_raw_event["start"]["dateTime"]
    del single_raw_event["end"]["dateTime"]
    parsed_events = parse_events([single_raw_event], args)
    expected_single_event.start = datetime.fromisoformat("2021-07-12")
    expected_single_event.is_not_day_event = False
    assert len(parsed_events) == 1
    assert parsed_events[0] == expected_single_event


def test_parse_event_no_password(
    args: Args, single_raw_event: dict, expected_single_event: MyEvent
):
    single_raw_event["location"] = "https://example.zoom.us/j/12345678987"
    parsed_event = parse_event(single_raw_event, args)
    expected_single_event.zoom_link = (
        "zoommtg://example.zoom.us/join?action=join&confno=12345678987"  # noqa: E501
    )
    assert parsed_event == expected_single_event


def test_parse_event_description(
    args: Args,
    single_raw_event_description_only: dict,
    expected_single_event_from_description: MyEvent,
):

    parsed_event = parse_event(single_raw_event_description_only, args)
    assert parsed_event == expected_single_event_from_description
