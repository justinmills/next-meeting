import argparse
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum


class Command(Enum):
    list = "list"
    join = "join"


class OutputFormat(Enum):
    stdout = "stdout"
    alfred = "alfred"


class NextMeetingOptions(Enum):
    """The options for what we found on your calendar"""

    # We found 1 meeting you should be in
    FoundNextMeeting = "FoundNextMeeting"
    # We found multiple meetings you should be in
    MultipleOptions = "MultipleOptions"
    # We didn't find any meeting you should be in
    NoOptions = "NoOptions"


@dataclass
class Args:
    # meeting: str = None
    # autojoin: bool = False
    command: Command
    format: OutputFormat = OutputFormat.stdout
    now: datetime = datetime.now(tz=timezone.utc)


def valid_datetime_type(arg_datetime_str: str) -> datetime:
    """custom argparse type for user datetime values given from the command line"""
    try:
        return datetime.fromisoformat(arg_datetime_str)
    except ValueError:
        msg = f"Given Datetime ({arg_datetime_str}) not valid! Expected ISO format, 'YYYY-MM-DDTHH:mm:ss.mmmmmmZ'!"  # noqa: E501
        raise argparse.ArgumentTypeError(msg)


def parse_args() -> Args:
    parser = argparse.ArgumentParser(
        description="Parse your calendar looking for the next zoom meeting"
    )
    parser.add_argument(
        "-c",
        "--command",
        dest="command",
        choices=tuple(e.value for e in Command),
        required=True,
        help="The command to run",
    )
    parser.add_argument(
        "-f",
        "--format",
        dest="format",
        default=OutputFormat.stdout.value,
        choices=tuple(e.value for e in OutputFormat),
        help="Format for the output",
    )
    parser.add_argument(
        "-n",
        "--now",
        dest="now",
        default=datetime.now(tz=timezone.utc),
        type=valid_datetime_type,
        help="Optional override time to use for 'now'",
    )
    args = parser.parse_args()
    return Args(
        command=Command[args.command],
        format=OutputFormat[args.format],
        now=args.now,
    )


def _debug(message: str, format: OutputFormat = OutputFormat.stdout) -> None:
    if format == OutputFormat.stdout:
        print(message)
    else:
        print(message, file=sys.stderr)


def _output(message: str) -> None:
    "Thin wrapper around print so we can debug what we're doing"
    print(message)