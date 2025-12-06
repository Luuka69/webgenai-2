from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class Column:
    id: str
    name: str
    type: str
    required: bool = False
    unique: bool = False
    enum_values: Optional[List[str]] = None
    default: Optional[Any] = None
    fk: Optional[Dict[str, Any]] = None  # {tableId, columnId}


@dataclass
class Table:
    id: str
    name: str
    columns: List[Column] = field(default_factory=list)


@dataclass
class DataSchema:
    id: str
    workflow_id: Optional[str]
    tables: List[Table]


@dataclass
class MigrationLog:
    id: str
    workflow_id: str
    operation: str  # ADD_COLUMN, CHANGE_TYPE, DELETE_COLUMN, RENAME_COLUMN
    table_id: str
    column_id: str
    old_config: Optional[Dict[str, Any]]
    new_config: Optional[Dict[str, Any]]
    created_at: Optional[str] = None
