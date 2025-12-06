from typing import Any, List, Optional

from pydantic import BaseModel, Field

from ai_engine.schemas.pydantic.data import DataSchema
from ai_engine.schemas.pydantic.relations import ScreenRelation
from ai_engine.schemas.pydantic.screen import ScreenSchema


class BindingSuggestion(BaseModel):
    field_id: Optional[str] = None
    column_id: Optional[str] = None
    confidence: Optional[float] = None
    rationale: Optional[str] = None
    accepted: bool = False

    class Config:
        extra = "allow"


class AIResponse(BaseModel):
    structure: Optional[ScreenSchema] = None
    code: str = ""
    data_schema: Optional[DataSchema] = None
    bindings: List[BindingSuggestion] = Field(default_factory=list)
    relations: List[ScreenRelation] = Field(default_factory=list)
    raw_response: Optional[str] = None

    class Config:
        extra = "allow"
