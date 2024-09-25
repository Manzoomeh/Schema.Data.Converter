from typing import List, Optional, Any
from pydantic import BaseModel, ConfigDict
from enum import Enum

class DataType(Enum):
    TEXT_VALUE = "textvalue"
    N_TEXT_VALE = "ntextvalue"
    NUM_VALUE = "numvalue"
    FLOAT_VALUE = "floatvalue"
    FIX_VALUE = "fixvalue"
    URL_VALUE = "urlvalue"
    FILE_VALUE = "filevalue"
    REFERENCE = "reference"

class FixValue(BaseModel):
    id: int
    value: Any

class Part(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    caption: Optional[str]
    datatype: Optional[DataType]
    fixvalues: Optional[List[FixValue]]

    Id: int

class Property(BaseModel):
    section: Optional[str]
    title: str
    multi: bool
    Id: int

    parts: List[Part]