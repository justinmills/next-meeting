from datetime import datetime

import pytest
from next_meeting.args import Args, Command, OutputFormat

from . import factories as f


@pytest.fixture
def now() -> datetime:
    return datetime(2021, 7, 19, 13, 0, 0, 0)


@pytest.fixture
def args(now) -> Args:
    return Args(command=Command.list, format=OutputFormat.alfred)


@pytest.fixture
def single_raw_event() -> dict:
    return f.single_raw_event()


@pytest.fixture
def single_raw_event_conferenceData() -> dict:
    return f.single_raw_event_conferenceData()
