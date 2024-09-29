from typing import Dict, Any, List, Optional
from models.questions import Property, Part, DataType, FixValue, Section
import aiohttp
from dataclasses import dataclass

@dataclass
class Schema:
    url: str
    paramUrl: str
    hashid: str
    version: str
    properties: Dict[int, Property]

async def get_fixes_from_link_async(url: str):
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as req:
            resp = await req.json()
    if not isinstance(resp, list):
        resp = list()
    return [
        FixValue(**item)
        for item in resp
    ]

class SchemaRepository:

    def __init__(self) -> None:
        self.__repo: Dict[str, Schema] = dict()

    async def get_async(self, schema_url: str, rkey: str, culture: str):
        if schema_url not in self.__repo:
            self.__repo[schema_url] = await self.__route_schema_async(schema_url, rkey, culture)
        return self.__repo[schema_url]
    
    def __set_datatype(self, view_type: str, validations: Optional[Dict]) -> Optional[DataType]:
        result = None        
        if view_type in ["select", "checklist", "radio"]:
            result = DataType.FIX_VALUE
        elif view_type == "textarea":
            result = DataType.N_TEXT_VALE
        elif view_type == "text":
            if validations is None:
                validations = dict()
            datatype = validations.get("dataType")
            if datatype == "int":
                result = DataType.NUM_VALUE
            elif datatype == "float":
                result = DataType.FLOAT_VALUE
            else:
                result = DataType.TEXT_VALUE
        elif view_type in ("autocomplete", "simpleautocomplete"):
            result = DataType.URL_VALUE
        elif view_type in ["upload", "blob"]:
            result = DataType.FILE_VALUE
        elif view_type == "color":
            result = DataType.TEXT_VALUE
        elif view_type in ("reference", "simplereference"):
            result = DataType.REFERENCE
        return result

    async def __route_schema_async(self, url: str, rkey: str, culture: str):
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as req:
                resp = await req.json()
        if not SchemaRepository.is_schema_base(resp):
            raise Exception("Invalid schemaUrl")
        schema_data = resp["sources"][0]["data"][0]
        hashid = schema_data["schemaId"]
        param_url = schema_data["paramUrl"]
        version = schema_data["schemaVersion"]
        questions: List[Dict] = schema_data.get("questions", list())
        sections: Dict[int, str] = {
            sec["id"]: sec["title"]
            for sec in schema_data.get("sections", list())
        }

        properties: Dict[int, Property] = dict()
        for q in questions:
            prp_id = int(q["prpId"])
            multi = bool(q.get("multi", False))
            parts = list()
            q_parts: List[Dict] = q.get("parts", list())
            for p in q_parts:
                view_type = p["viewType"]
                part_id = int(p["part"])
                link = str(p.get("link") or "").replace("${rkey}", rkey).replace("${culture}", culture)
                data_type = self.__set_datatype(view_type, p.get("validations"))
                if data_type is None:
                    print("[Warning]", f"Datatype not set for prpId={prp_id} and partId={part_id}")
                if data_type == DataType.FIX_VALUE:
                    if link is not None:
                        fix_values = await get_fixes_from_link_async(link)
                    else:
                        fix_values = [
                            FixValue(**item)
                            for item in p["fixValues"]
                        ]
                else:
                    fix_values = list()
                parts.append(
                    Part(
                        caption=p.get("caption"),
                        Id=part_id,
                        datatype=data_type,
                        link=link,
                        fixvalues=fix_values
                    )
                )
                
            properties[prp_id] = Property(
                section=sections.get(int(q.get("sectionId", 0))),
                title=str(q["title"]),
                multi=multi,
                Id=prp_id,
                parts=parts
            )
        return Schema(
            url=url,
            paramUrl=param_url,
            version=version,
            hashid=hashid,
            properties=properties
        )

    @staticmethod
    def is_schema_base(data: Any):
        if isinstance(data, Dict):
            sources = data.get("sources")
            if isinstance(sources, list) and len(sources) > 0:
                source = sources[0]
                if isinstance(source, dict):
                    data = source.get("data")
                    if isinstance(data, list) and len(data) > 0:
                        data = data[0]
                        if "schemaId" in data and "paramUrl" in data:
                            return True
        return False
        
