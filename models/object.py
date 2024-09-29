from typing import Any, List, Dict
from pydantic import BaseModel, ConfigDict
from models.questions import Property, DataType, Part
import aiohttp

async def get_autocomplete_id_async(link: str, term: Any):
    url = link.replace("${term}", term)
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as req:
            resp = await req.json()
    if not isinstance(resp, list):
        resp = list()
    for item in resp:
        if item["value"] == term:
            return int(item["id"])


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
        self.__autocomplete_repo: Dict[Part, Dict[str, int]] = dict()

    async def add_prpvalue_async(self, prpvalues: List[ObjectPrpValue]):
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
                        raise Exception(f"Invalid value for prpId={prpid} and part={input_part}. Info: [value='{input_value}' not found in fixvalues]")
                    input_value = selected_id
                elif part_datatype in (DataType.URL_VALUE):
                    # GET FROM LINK ( --- DEPENDENCIES ???)
                    if selected_part not in self.__autocomplete_repo:
                        self.__autocomplete_repo[selected_part] = dict()
                    part_repo = self.__autocomplete_repo[selected_part]
                    if input_value not in part_repo:
                        autocomplete_id = await get_autocomplete_id_async(selected_part.link, input_value)
                        if autocomplete_id is None:
                            raise Exception(f"Invalid value for prpId={prpid} and part={input_part}. Info: [value='{input_value}' not found in autocomplete]")
                        part_repo[input_value] = autocomplete_id
                    input_value = part_repo[input_value]
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
