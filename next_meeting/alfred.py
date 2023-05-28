import json
from dataclasses import asdict, dataclass, field, is_dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Union

# Classes to help serialize various Alfred formats


class EnhancedJSONEncoder(json.JSONEncoder):
    def default(self, o: Any) -> Any:
        if is_dataclass(o):
            return asdict(o)
        elif isinstance(o, datetime):
            return o.isoformat()
        return super().default(o)


@dataclass
class ItemIcon:
    path: str


@dataclass
class Item:
    uid: str
    title: str
    subtitle: str
    arg: Optional[str] = None
    variables: Optional[Dict[str, Optional[Any]]] = None
    icon: Optional[ItemIcon] = None


@dataclass
class ScriptFilterOutput:
    """Script Filter Output format

    Reference: https://www.alfredapp.com/help/workflows/inputs/script-filter/json/"""

    items: List[Item] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(self, indent=2, cls=EnhancedJSONEncoder)


@dataclass
class AlfredWorkflow:
    """Internal object JSON Utility format

    arg is the input (query) for the next component. We set this to be a
    serialized JSON object of type ScriptFilterOutput. We do this so we can (if
    need be) feed the output of a Run Script into a Script Filter component to
    allow the user to select. This is useful in the case where there are
    multiple meetings to join and the user needs to be presented with each
    option.

    Reference: https://www.alfredapp.com/help/workflows/utilities/json/"""

    arg: str
    config: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, Optional[Union[str, bool, datetime]]]] = None


@dataclass
class JsonUtilityFormat:
    """Alfred workflow output - JSON Utility

    We use this as the output of a Run Script Action.

    Reference: https://www.alfredapp.com/help/workflows/utilities/json/"""

    alfredworkflow: AlfredWorkflow

    def to_json(self) -> str:
        return json.dumps(self, indent=2, cls=EnhancedJSONEncoder)
