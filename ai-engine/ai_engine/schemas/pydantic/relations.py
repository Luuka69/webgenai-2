from typing import Any, Dict, Optional

from pydantic import BaseModel, Field


class ScreenRelation(BaseModel):
    id: Optional[str] = None
    from_screen_id: str
    to_screen_id: str
    relation_type: str  # navigate, edit, lookup, collection, wizardNext
    data: Dict[str, Any] = Field(default_factory=dict)

    class Config:
        extra = "allow"
