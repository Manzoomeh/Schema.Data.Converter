from typing import List, Optional, Any
from pydantic import BaseModel
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

class FixValue:
    id: int
    value: Any

class Part(BaseModel):
    caption: Optional[str]
    datatype: DataType
    fixvalues: Optional[List[FixValue]]

    Id: int

class Property(BaseModel):
    section: Optional[str]
    title: str
    multi: bool
    Id: int

    parts: List[Part]