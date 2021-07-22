import pytest
from next_meeting.args import Args, NextMeetingOptions
from next_meeting.main import command_list

from . import factories as f
from unittest.mock import patch, MagicMock


@pytest.fixture
def mock_fetch_events() -> MagicMock:
    with patch("next_meeting.main.fetch_events") as p:
        yield p


def test_command_list_empty(mock_fetch_events: MagicMock, args: Args):
    mock_fetch_events.return_value = []
    command_list(args)
