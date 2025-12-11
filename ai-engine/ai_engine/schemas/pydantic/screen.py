from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class Component(BaseModel):
    id: Optional[str] = None
    type: str
    label: Optional[str] = None
    props: Dict[str, Any] = Field(default_factory=dict)
    position: Dict[str, Any] = Field(default_factory=dict)
    style: Dict[str, Any] = Field(default_factory=dict)
    bindings: Dict[str, Any] = Field(default_factory=dict)
    validation: Dict[str, Any] = Field(default_factory=dict)
    children: Optional[List["Component"]] = None  # nested components

    class Config:
        extra = "allow"


class ScreenSchema(BaseModel):
    id: Optional[str] = None
    name: Optional[str] = None
    workflow_id: Optional[str] = None
    layout: Optional[Dict[str, Any]] = None
    components: List[Component] = Field(default_factory=list)
    theme: Optional[Dict[str, Any]] = None
    status: str = "draft"
    version: int = 1
    metadata: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"
