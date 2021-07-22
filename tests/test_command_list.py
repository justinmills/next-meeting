from unittest.mock import MagicMock, patch

import pytest
from next_meeting.args import Args
from next_meeting.main import command_list


@pytest.fixture
def mock_fetch_events() -> MagicMock:
    with patch("next_meeting.main.fetch_events") as p:
        yield p


def test_command_list_empty(mock_fetch_events: MagicMock, args: Args):
    mock_fetch_events.return_value = []
    command_list(args)
