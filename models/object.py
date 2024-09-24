from typing import Any, List
from pydantic import BaseModel, ConfigDict
from models.questions import Property, DataType

class ObjectValue(BaseModel):
    part: int
    value: Any

class ObjectPrpValue(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    prp: Property
    values: List[ObjectValue]

class ObjectProperties:
    def __init__(self) -> None:
        self.data = dict()

    def add_prpvalue(self, prpvalues: List[ObjectPrpValue]):
        for prpvalue in prpvalues:
            prp = prpvalue.prp
            prpid = prp.Id
            added_parts = list()
            for val in prpvalue.values: 
                input_part = val.part
                selected_part = None
                for part in prp.parts:
                    if part.Id == input_part:
                        selected_part = part
                        break
                if selected_part is None:
                    raise Exception(f"Invalid part={input_part} for prpId={prpid}")
                input_value = val.value
                part_datatype = selected_part.datatype
                if part_datatype == DataType.FIX_VALUE:
                    fixvalues = selected_part.fixvalues
                    if not isinstance(fixvalues, list):
                        raise Exception(f"Invalid part! datatype={part_datatype.value} but fixvalues not found")
                    selected_id = None
                    for item in fixvalues:
                        if item.value == input_value:
                            selected_id = item.id
                            break
                    if selected_id is None:
                        raise Exception(f"Invalid value for prpId={input_part} and part={prpid}. Info: [value='{input_value}' not found in fixvalues]")
                    input_value = selected_id
                elif part_datatype in (DataType.REFERENCE, DataType.URL_VALUE):
                    raise NotImplementedError(f"datatype={part_datatype.value} not implemented yet")
                added_parts.append({
                    "part": input_part,
                    "values": [
                        {
                            "value": input_value
                        }
                    ]
                })
            if len(added_parts) > 0:
                if prpid not in self.data:
                    self.data[prpid] = {
                        "propId": prpid,
                        "multi": prp.multi,
                        "added": [
                            {
                                "parts": added_parts
                            }
                        ]
                    }
                else:
                    if prp.multi:
                        self.data[prpid]["added"].append({
                            "parts": added_parts
                        })
                    else:
                        raise Exception(f"prpId={prpid} is not a multi properties")
