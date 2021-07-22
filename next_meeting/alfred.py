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
    """Script Filter Output format"""

    items: List[Item] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(self, indent=2, cls=EnhancedJSONEncoder)


@dataclass
class AlfredWorkflow:
    arg: str
    config: Optional[Dict[str, str]] = None
    variables: Optional[Dict[str, Optional[Union[str, bool, datetime]]]] = None


@dataclass
class JsonUtilityFormat:
    """Alfred workflow output - JSON Utility"""

    alfredworkflow: AlfredWorkflow

    def to_json(self) -> str:
        return json.dumps(self, indent=2, cls=EnhancedJSONEncoder)
