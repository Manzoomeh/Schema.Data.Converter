from abc import ABC, abstractmethod
from typing import Dict, List, Generic, TypeVar
from models.schema import Schema
from models.object import ObjectProperties

IMPORT_DATA = TypeVar("IMPORT_DATA")
EXPORT_DATA = TypeVar("EXPORT_DATA")

class ProviderError(Exception): ...

class IProvider(Generic[IMPORT_DATA, EXPORT_DATA]):

    def __init__(self, schema: Schema) -> None:
        super().__init__()
        self._schema = schema
        self._schema_paramUrl = self._schema.paramUrl
        self._schema_version = self._schema.version
        self._schema_hashid = self._schema.hashid
        self._schema_url = self._schema.url
        self._properties = self._schema.properties

    @abstractmethod
    def _create_export_data(self, data: Dict) -> EXPORT_DATA: ...

    @abstractmethod
    def _create_import_data(self, data: Dict) -> IMPORT_DATA: ...
    
    @abstractmethod
    def _export_schema(self, export_data: EXPORT_DATA) -> List[ObjectProperties]: ...

    @abstractmethod
    async def _import_schema_async(self, properties: List[ObjectProperties], import_data: IMPORT_DATA): ...

    def export_schema(self, data: Dict) -> List[ObjectProperties]:
        return self._export_schema(
            self._create_export_data(data)
        )
    
    async def import_schema_async(self, properties: List[ObjectProperties], data: Dict):
        return await self._import_schema_async(
            properties,
            self._create_import_data(data)
        )
