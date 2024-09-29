from typing import Dict, List, Union, Tuple
from models.object import ObjectProperties, ObjectPrpValue, ObjectValue
from models.schema import Schema
from .interface import IProvider, ProviderError
from pydantic import BaseModel, field_validator, model_validator, ConfigDict
from pathlib import Path
import pandas

class ExcelExportData(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)
    file_path: str
    name: str
    headers: List[str] = [
        "property",
        "part"
    ]

    @field_validator("file_path")
    def check_file_path(cls, value: str):
        if not Path(value).is_dir():
            raise ValueError("Invalid file path")
        return value
    
    @field_validator("headers")
    def check_headers(cls, value: List[str]):
        ret_val: List[str] = list()
        if "section" in value:
            ret_val.append("section")
        if "property" in value:
            ret_val.append("property")
        else:
            raise ValueError("'property' should be in headers")
        if "part" in value:
            ret_val.append("part")

        return ret_val
    
    @model_validator(mode="after")
    def check_file_is_exist(self):
        if not self.io.is_file():
            raise ValueError("Source file not found")
        return self
        
    @property
    def io(self):
        return Path(self.file_path).joinpath(self.name)

class ExcelImportData(BaseModel): ...

class ExcelProvider(IProvider[ExcelImportData, ExcelExportData]):

    ROW_NUMBER = "RowNumber"

    def __init__(self, schema: Schema) -> None:
        super().__init__(schema)
    
    def _create_export_data(self, data: Dict) -> ExcelExportData:
        return ExcelExportData(**data)
    
    def _create_import_data(self, data: Dict) -> ExcelImportData:
        return ExcelImportData(**data)
    
    async def _import_schema_async(self, properties: List[ObjectProperties], import_data: ExcelImportData):
        return await super()._import_schema_async(properties, import_data)
    
    async def _export_schema_async(self, export_data: ExcelExportData) -> List[ObjectProperties]:
        headers = export_data.headers
        headers_count = len(headers)
        df = pandas.read_excel(io=export_data.io, header=list(range(headers_count)), dtype=pandas.StringDtype.name)
        columns: List[Union[str, Tuple[str]]] = df.columns
        raw_columns: List[str] = list()
        if ExcelProvider.ROW_NUMBER not in columns[0]:
            raise ValueError(f"First column should be '{ExcelProvider.ROW_NUMBER}'")
        raw_columns.append(ExcelProvider.ROW_NUMBER)
        for index, col in enumerate(columns[1:]):
            if isinstance(col, str):
                col = (col, )
            col_data = {
                "section": None,
                "property": None,
                "part": None
            }
            for index, title in enumerate(col):
                if title.startswith(f"Unnamed: "):
                    title = None
                col_data[headers[index]] = title
            named_col = self.__get_named_col(col_data)
            if named_col is None:
                raise ProviderError("Invalid columns")
                
            raw_columns.append(named_col)
        df.columns = raw_columns
        objects_properties: Dict[int, ObjectProperties] = dict()
        selected_id = None
        for index, row in df.iterrows():
            row_id = row[ExcelProvider.ROW_NUMBER]
            if pandas.notna(row_id):
                selected_id = int(row_id)
            if selected_id not in objects_properties:
                objects_properties[selected_id] = ObjectProperties()
            prpvalues: Dict[int, ObjectPrpValue] = dict()
            for col in df.columns[1:]:
                col_val = row[col]
                if pandas.notna(col_val):
                    prpid, part = col.split("_")
                    prpid = int(prpid)
                    part = int(part)
                    if prpid not in prpvalues:
                        prpvalues[prpid] = ObjectPrpValue(
                            prp=self._properties[prpid],
                            values=[]
                        )
                    prpvalues[prpid].values.append(
                        ObjectValue(
                            part=part,
                            value=col_val
                        )
                    )
            try:
                await objects_properties[selected_id].add_prpvalue_async(list(prpvalues.values()))
            except Exception as ex:
                print(f"[Warning] row={index} has error! Info: {str(ex)}")

        return list(objects_properties.values())

    def __get_named_col(self, col_data: Dict):
        for prpid, prp in self._properties.items():
            if col_data["property"] == prp.title and col_data["section"] == prp.section:
                if col_data["part"] is not None:
                    parts = prp.parts
                    for p in parts:
                        if col_data["part"] == p.caption:
                            part = p.Id
                else:
                    part = 1
                return f"{prpid}_{part}"
    