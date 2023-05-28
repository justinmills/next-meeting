from next_meeting.args import Args, NextMeetingOptions
from next_meeting.main import find_meeting_to_join

from . import factories as f


def test_no_events(args):
    options, event = find_meeting_to_join(list(), args)
    assert options == NextMeetingOptions.NoOptions
    assert event is None


def test_in_progress_only(args: Args):
    event = f.sample_my_event()
    event.in_progress = True
    assert event.is_next_joinable is False

    options, actual = find_meeting_to_join([event], args)

    assert options == NextMeetingOptions.FoundNextMeeting
    assert actual == event


def test_next_only(args: Args):
    event = f.sample_my_event()
    event.is_next_joinable = True
    assert event.in_progress is False

    options, actual = find_meeting_to_join([event], args)

    assert options == NextMeetingOptions.FoundNextMeeting
    assert actual == event


def test_in_progress_and_next(args: Args):
    event1 = f.sample_my_event()
    event2 = f.sample_my_event()
    event1.in_progress = True
    event2.is_next_joinable = True
    assert event1.is_next_joinable is False
    assert event2.in_progress is False

    options, to_join = find_meeting_to_join([event1, event2], args)

    assert options == NextMeetingOptions.FoundNextMeeting
    assert to_join == event2


def test_multiple_in_progress(args: Args):
    events = [f.sample_my_event(), f.sample_my_event()]
    for e in events:
        e.in_progress = True
        assert e.is_next_joinable is False

    options, to_join = find_meeting_to_join(events, args)

    assert options == NextMeetingOptions.MultipleOptions
    assert to_join is None


def test_multiple_is_next_joinable(args: Args):
    events = [f.sample_my_event(), f.sample_my_event()]
    for e in events:
        e.is_next_joinable = True
        assert e.in_progress is False

    options, to_join = find_meeting_to_join(events, args)

    assert options == NextMeetingOptions.MultipleOptions
    assert to_join is None


def test_multiple_in_progress_one_up_next(args: Args):
    events = [f.sample_my_event(), f.sample_my_event()]
    for e in events:
        e.in_progress = True
        assert e.is_next_joinable is False
    next = f.sample_my_event()
    next.is_next_joinable = True
    assert next.in_progress is False
    events.append(next)

    options, to_join = find_meeting_to_join(events, args)

    assert options == NextMeetingOptions.FoundNextMeeting
    assert to_join is next
