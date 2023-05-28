from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock, patch

import pytest

from next_meeting.alfred import AlfredWorkflow, JsonUtilityFormat, ScriptFilterOutput
from next_meeting.args import Args, NextMeetingOptions
from next_meeting.main import command_list
from next_meeting.parsing import MyEvent


@pytest.fixture
def mock_fetch_events() -> MagicMock:
    with patch("next_meeting.main.fetch_events") as p:
        yield p


def test_command_list_empty(mock_fetch_events: MagicMock, args: Args, capsys):
    mock_fetch_events.return_value = []
    command_list(args)
    captured: str = capsys.readouterr()
    expected: JsonUtilityFormat = JsonUtilityFormat(
        alfredworkflow=AlfredWorkflow(
            arg=ScriptFilterOutput(items=[]).to_json(),
            config=dict(),
            variables=dict(
                need_to_prompt=True, next_meeting=NextMeetingOptions.NoOptions.value
            ),
        )
    )
    expected_output: str = expected.to_json() + "\n"
    assert expected_output == captured.out


def test_command_list_meeting_to_join(
    mock_fetch_events: MagicMock, args: Args, single_raw_event: dict, capsys
):
    # Set now so we select this meeting to join next.
    args.now = datetime(2021, 7, 12, 13, 29, 0, 0, tzinfo=timezone.utc)

    mock_fetch_events.return_value = [single_raw_event]
    command_list(args)
    captured: str = capsys.readouterr()
    my_event: MyEvent = MyEvent(
        id="77gcalEventId_20210712T133000Z",
        start=datetime(2021, 7, 12, 9, 30, 00, tzinfo=timezone(-timedelta(hours=4))),
        summary="JIRA Board Review",
        meeting_link="zoommtg://example.zoom.us/join?action=join&confno=12345678987&pwd=SUPERSECRET1234",
        icon="icon.png",
    )
    expected: JsonUtilityFormat = JsonUtilityFormat(
        alfredworkflow=AlfredWorkflow(
            arg=ScriptFilterOutput(items=[my_event.to_item()]).to_json(),
            config=dict(),
            variables=dict(
                need_to_prompt=True,
                next_meeting=NextMeetingOptions.FoundNextMeeting.value,
                zoom_link="zoommtg://example.zoom.us/join?action=join&confno=12345678987&pwd=SUPERSECRET1234",
                title="JIRA Board Review",
                start="2021-07-12T09:30:00-04:00",
            ),
        )
    )
    expected_output: str = expected.to_json() + "\n"
    assert expected_output == captured.out
