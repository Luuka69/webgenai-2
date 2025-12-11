from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Column(BaseModel):
    id: str
    name: str
    type: str
    required: bool = False
    unique: bool = False
    enum_values: Optional[List[str]] = None
    default: Optional[Any] = None
    fk: Optional[Dict[str, Any]] = None  # {tableId, columnId}

    class Config:
        extra = "allow"


class Table(BaseModel):
    id: str
    name: str
    columns: List[Column] = Field(default_factory=list)

    class Config:
        extra = "allow"


class DataSchema(BaseModel):
    id: Optional[str] = None
    workflow_id: Optional[str] = None
    tables: List[Table] = Field(default_factory=list)

    class Config:
        extra = "allow"


class MigrationLog(BaseModel):
    id: str
    workflow_id: str
    operation: str
    table_id: str
    column_id: str
    old_config: Optional[Dict[str, Any]] = None
    new_config: Optional[Dict[str, Any]] = None
    created_at: Optional[str] = None

    class Config:
        extra = "allow"
