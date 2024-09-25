
from typing import Dict, List, Optional
from models.object import ObjectProperties
from models.schema import Schema
from .interface import IProvider
from pydantic import BaseModel
import aiohttp

class ApiImportData(BaseModel):
    url: str
    body: Optional[dict]

class ApiExportData(BaseModel): ...


class ApiProvider(IProvider[ApiImportData, ApiExportData]):
    def __init__(self, schema: Schema) -> None:
        super().__init__(schema)

    def _create_import_data(self, data: Dict) -> ApiImportData:
        return ApiImportData(**data)

    def _create_export_data(self, data: Dict) -> ApiExportData:
        return super()._create_export_data(data)

    def _export_schema(self, export_data: ApiExportData) -> List[ObjectProperties]:
        return super()._export_schema(export_data)          

    async def _import_schema_async(self, properties: List[ObjectProperties], import_data: ApiImportData):
        async with aiohttp.ClientSession() as session:
            body = import_data.body or dict()
            for obj_properties in properties:
                copy_body = body.copy()
                copy_body.update({
                    "data": {
                        "paramUrl": self._schema_paramUrl,
                        "properties": list(obj_properties.data.values()),
                        "schemaId": self._schema_hashid,
                        "schemaVersion": self._schema_version
                    }
                })
                print(copy_body)
                async with session.post(url=import_data.url, json=copy_body) as req:
                    response = await req.json()

                    print(response)

            


            
