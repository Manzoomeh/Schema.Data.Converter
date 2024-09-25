from typing import Dict, List
from models.object import ObjectProperties
from models.schema import Schema
from .interface import IProvider
from pydantic import BaseModel

class SqlImportData(BaseModel): ...

class SqlExportData(BaseModel): ...

class SqlProvider(IProvider[SqlImportData, SqlExportData]):

    def __init__(self, schema: Schema) -> None:
        super().__init__(schema)

    def _create_import_data(self, data: Dict) -> SqlImportData:
        return super()._create_import_data(data)
    
    def _create_export_data(self, data: Dict) -> SqlExportData:
        return super()._create_export_data(data)
    
    async def _import_schema_async(self, properties: List[ObjectProperties], import_data: SqlImportData):
        return await super()._import_schema_async(properties, import_data)
    
    def _export_schema(self, export_data: SqlExportData) -> List[ObjectProperties]:
        return super()._export_schema(export_data)
    