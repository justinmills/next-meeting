from datetime import datetime
from typing import Dict, List, Optional, Tuple, Union

from .alfred import AlfredWorkflow, JsonUtilityFormat, ScriptFilterOutput
from .args import (
    Args,
    Command,
    NextMeetingOptions,
    OutputFormat,
    _debug,
    _output,
    parse_args,
)
from .gcal import fetch_events
from .parsing import MyEvent, _debug_event_list, parse_events


def find_meeting_to_join(
    events: List[MyEvent], args: Args
) -> Tuple[NextMeetingOptions, Optional[MyEvent]]:
    """
    Given a list of meetings to join, find the one we should join

    ...but this will only do so if the meeting to join is "obvious". Meaning
    there aren't multiple meetings happening at the same time (with some
    caveats) and that the next meeting is starting eminently.
    """
    _debug(f"Looking for next meeting. Have {len(events)} candidates", args.format)
    if events:
        in_progress = [e for e in events if e.in_progress]
        next = [e for e in events if e.is_next_joinable]
        if len(next) == 1:
            return NextMeetingOptions.FoundNextMeeting, next[0]
        if len(in_progress) == 1:
            return NextMeetingOptions.FoundNextMeeting, in_progress[0]

        # Too much ambiguity, display the list downstream for the user to pick.
        return NextMeetingOptions.MultipleOptions, None

    return NextMeetingOptions.NoOptions, None


def command_list(args: Args) -> None:
    """Implement the list command"""
    all_events = fetch_events(args)
    events: List[MyEvent] = parse_events(all_events, args)

    _debug_event_list(events, args.format)

    filtered_events = [e for e in events if e.is_not_day_event and e.zoom_link]

    if args.format == OutputFormat.alfred:
        items = [e.to_item() for e in filtered_events]
        output = ScriptFilterOutput(items=items)
        next_meeting_value, to_join = find_meeting_to_join(filtered_events, args)
        vars: Dict[str, Optional[Union[str, bool, datetime]]] = dict(
            # bool values show up as 0/1 in Alfred.
            need_to_prompt=True,
            next_meeting=next_meeting_value.value,
        )
        if to_join:
            vars.update(
                zoom_link=to_join.zoom_link,
                title=to_join.summary,
                start=to_join.start,
            )
        utility_output = JsonUtilityFormat(
            alfredworkflow=AlfredWorkflow(
                arg=output.to_json(),
                config=dict(),
                variables=vars,
            )
        )
        _output(utility_output.to_json())
    else:
        _output("TODO: Figure out the non-alfred output format...")


def entrypoint() -> None:
    args: Args = parse_args()

    if args.command == Command.list:
        command_list(args)
    elif args.command == Command.join:
        pass
    else:
        pass
