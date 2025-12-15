from datetime import datetime
from typing import Any, Optional, List

from pydantic import BaseModel, Field


class Wf(BaseModel):
    id_client: int = Field(..., alias="ID_CLIENT", description="Client id (PK)")
    id_wf: str = Field(..., alias="ID_WF", description="Workflow id (PK)")
    nom_wf: Optional[str] = Field(None, alias="NOM_WF")
    load_wf: Optional[Any] = Field(None, alias="LOAD_WF", description="Serialized workflow definition or file path (BLOB)")
    default_where_wf: Optional[Any] = Field(None, alias="DEFAULT_WHERE_WF", description="Workflow-level default filter/where (BLOB)")
    created_at: Optional[datetime] = Field(None, alias="CREATED_AT")
    updated_at: Optional[datetime] = Field(None, alias="UPDATED_AT")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"


class TacheWf(BaseModel):
    id_client: int = Field(..., alias="ID_CLIENT")
    id_wf: str = Field(..., alias="ID_WF")
    id_tache: str = Field(..., alias="ID_TACHE")
    nom_tache: Optional[str] = Field(None, alias="NOM_TACHE")
    active_tache: str = Field("O", alias="ACTIVE_TACHE", description="'O' active / 'N' inactive")
    condition_active_tache: Optional[Any] = Field(None, alias="CONDITION_ACTIVE_TACHE", description="Activation condition (BLOB)")
    load_tache: Optional[Any] = Field(None, alias="LOAD_TACHE", description="Serialized task config (BLOB)")
    default_where_tache: Optional[Any] = Field(None, alias="DEFAULT_WHERE_TACHE", description="Task-level default filter/where (BLOB)")
    created_at: Optional[datetime] = Field(None, alias="CREATED_AT")
    updated_at: Optional[datetime] = Field(None, alias="UPDATED_AT")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"


class IhmWf(BaseModel):
    id_client: int = Field(..., alias="ID_CLIENT")
    id_wf: str = Field(..., alias="ID_WF")
    id_tache: str = Field(..., alias="ID_TACHE")
    id_ihm: str = Field(..., alias="ID_IHM")
    nom_ihm: Optional[str] = Field(None, alias="NOM_IHM")
    load_ihm: Optional[Any] = Field(None, alias="LOAD_IHM", description="Serialized screen description (WebGen schema + HTML) (BLOB)")
    default_where_ihm: Optional[Any] = Field(None, alias="DEFAULT_WHERE_IHM", description="Screen-level default filter/where (BLOB)")
    created_at: Optional[datetime] = Field(None, alias="CREATED_AT")
    updated_at: Optional[datetime] = Field(None, alias="UPDATED_AT")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"


class TabIhmWf(BaseModel):
    id_client: Optional[int] = Field(None, alias="ID_CLIENT")
    id_wf: Optional[str] = Field(None, alias="ID_WF")
    id_tache: Optional[str] = Field(None, alias="ID_TACHE")
    id_ihm: Optional[str] = Field(None, alias="ID_IHM")
    id_tab: str = Field(..., alias="ID_TAB")
    type_tab: str = Field("M", alias="TYPE_TAB", description="'M' master / 'D' detail")
    id_tab_maitre: Optional[str] = Field(None, alias="ID_TAB_MAITRE", description="Master table id when this is a detail table")
    load_tab: Optional[Any] = Field(None, alias="LOAD_TAB", description="Table creation script or JSON schema (BLOB)")
    default_where_tab: Optional[Any] = Field(None, alias="DEFAULT_WHERE_TAB", description="Default filter for this table (BLOB)")
    created_at: Optional[datetime] = Field(None, alias="CREATED_AT")
    updated_at: Optional[datetime] = Field(None, alias="UPDATED_AT")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"


class TabDetailIhmWf(BaseModel):
    id_client: Optional[int] = Field(None, alias="ID_CLIENT")
    id_wf: Optional[str] = Field(None, alias="ID_WF")
    id_tache: Optional[str] = Field(None, alias="ID_TACHE")
    id_ihm: Optional[str] = Field(None, alias="ID_IHM")
    id_tab: str = Field(..., alias="ID_TAB", description="Detail table id")
    id_tab_maitre: str = Field(..., alias="ID_TAB_MAITRE", description="Master table id")
    id_elem_tab: Optional[str] = Field(None, alias="ID_ELEM_TAB", description="Detail FK column pointing to master")
    id_elem_tab_maitre: Optional[str] = Field(None, alias="ID_ELEM_TAB_MAITRE", description="Master PK column")
    created_at: Optional[datetime] = Field(None, alias="CREATED_AT")
    updated_at: Optional[datetime] = Field(None, alias="UPDATED_AT")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"


class ElementIhmWf(BaseModel):
    id_client: Optional[int] = Field(None, alias="ID_CLIENT")
    id_wf: Optional[str] = Field(None, alias="ID_WF")
    id_tache: Optional[str] = Field(None, alias="ID_TACHE")
    id_ihm: Optional[str] = Field(None, alias="ID_IHM")
    id_tab: str = Field(..., alias="ID_TAB")
    id_element: str = Field(..., alias="ID_ELEMENT")
    type_element: Optional[str] = Field(None, alias="TYPE_ELEMENT", description="input/select/date/checkbox/grid/etc.")
    longueur_element: Optional[str] = Field(None, alias="LONGEUR_ELEMENT", description="Length/size hint")
    sql_lov_element: Optional[Any] = Field(None, alias="SQL_LOV_ELEMENT", description="SQL or JSON for list-of-values (BLOB)")
    enum_values: Optional[List[str]] = Field(None, alias="ENUM_VALUES", description="Explicit list of values for select/radio elements")
    transit: str = Field("N", alias="TRANSIT", description="'O' to pass values/navigation, 'N' otherwise")
    position_x: Optional[int] = Field(None, alias="POSITION_X")
    position_y: Optional[int] = Field(None, alias="POSITION_Y")
    hint_element: Optional[str] = Field(None, alias="HINT_ELEMENT", description="Tooltip/help text")
    control_element: Optional[Any] = Field(None, alias="CONTROL_ELEMENT", description="Extra control metadata (BLOB)")
    validateur_element: Optional[Any] = Field(None, alias="VALIDATEUR_ELEMENT", description="Validators/rules (BLOB)")
    default_value_element: Optional[Any] = Field(None, alias="DEFAULT_VALUE_ELEMENT", description="Default value expression (BLOB)")
    active: str = Field("O", alias="ACTIVE", description="'O' visible/active, 'N' hidden/inactive")
    codition_active: Optional[Any] = Field(None, alias="CODITION_ACTIVE", description="Conditional visibility/activation (BLOB)")
    created_at: Optional[datetime] = Field(None, alias="CREATED_AT")
    updated_at: Optional[datetime] = Field(None, alias="UPDATED_AT")

    class Config:
        allow_population_by_field_name = True
        extra = "allow"
