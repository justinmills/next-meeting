import next_meeting.gcal as gcal
from next_meeting.args import Args
from unittest.mock import MagicMock, patch


@patch("next_meeting.gcal.build")
@patch("next_meeting.gcal._fetch_creds")
def test_fetch_events(mock_fetch_creds, mock_build: MagicMock, args: Args):
    creds = MagicMock(name="Credentials")
    mock_fetch_creds.return_value = creds
    mock_service = MagicMock(name="GoogleService")
    mock_build.return_value = mock_service
    mock_events_list = dict(items=[{}])
    mock_service.events().list().execute.return_value = mock_events_list

    events = gcal.fetch_events(args)
    assert events == [{}]
    mock_build.assert_called_once_with("calendar", "v3", credentials=creds)
