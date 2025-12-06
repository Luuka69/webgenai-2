from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Component:
    id: str
    type: str
    label: Optional[str] = None
    props: Dict[str, Any] = field(default_factory=dict)
    position: Dict[str, Any] = field(default_factory=dict)  # row, col, rowSpan, colSpan
    style: Dict[str, Any] = field(default_factory=dict)
    bindings: Dict[str, Any] = field(default_factory=dict)  # columnId, actionId, etc.
    validation: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ScreenSchema:
    id: str
    name: Optional[str]
    workflow_id: Optional[str]
    layout: Dict[str, Any]
    components: List[Component]
    theme: Optional[Dict[str, Any]] = None
    status: str = 'draft'
    version: int = 1
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BindingSuggestion:
    field_id: str
    column_id: str
    confidence: float
    rationale: Optional[str] = None
    accepted: bool = False


@dataclass
class ScreenRelation:
    id: str
    from_screen_id: str
    to_screen_id: str
    relation_type: str  # navigate, edit, lookup, collection, wizardNext
    data: Dict[str, Any] = field(default_factory=dict)  # fkTableId, fkColumnId, filters, etc.
