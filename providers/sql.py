from typing import Dict, List
from bclib.parser import Answer
from models.schema import Schema
from models.rkey import RkeyContext
from .interface import IProvider
from pydantic import BaseModel
import pyodbc

class SqlImportData(BaseModel):
    address: str
    database: str
    username: str
    password: str
    lid: int
    ownerid: int
    userid: int

class SqlExportData(BaseModel): ...

class SqlProvider(IProvider[SqlImportData, SqlExportData]):

    def __init__(self, schema: Schema) -> None:
        super().__init__(schema)

    def _create_import_data(self, data: Dict) -> SqlImportData:
        return SqlImportData(**data)
    
    def _create_export_data(self, data: Dict) -> SqlExportData:
        return super()._create_export_data(data)
    
    async def _import_schema_async(self, rkey_context: RkeyContext, answers: List[Answer], import_data: SqlImportData):
        lid = import_data.lid
        lid_0_datatypes = ("fixvalue", "numvalue", "floatvalue", "files")
        for ans in answers:
            if await ans.is_valid_answer_async():
                added_actions = await ans.get_added_actions_async()
                with pyodbc.connect(
                    f"DRIVER={{SQL DRIVER}};SERVER={import_data.address};DATABASE={import_data.database};UID={import_data.username};PWD={import_data.password}"
                ) as db:
                    with db.cursor() as cursor:
                        cursor.execute("""
                        insert into Maintable (ownerid, [ord], creator, schemaid, hashid)
                        values (?, 1000, ?, ?, ?)
                        """, rkey_context.ownerid, rkey_context.userid, 0, self._schema_hashid)
                        usedforid = int(cursor.execute("SELECT @@IDENTITY AS ID").fetchone()[0])
                        for same_prp_id_objects in added_actions:
                            for same_prp_value_objects in same_prp_id_objects:
                                prp_value_id = same_prp_value_objects[0].prp_value_id
                                all_fix = True
                                for item in same_prp_value_objects:
                                    if item.datatype not in lid_0_datatypes:
                                        all_fix = False
                                        break
                                for data in same_prp_value_objects:
                                    if prp_value_id is None:
                                        cursor.execute(f"""
                                        INSERT INTO prpvalues (usedforid, PropertyID, lid, Ord, typeid, wordid, ownerid)
                                        VALUES (?, ?, ?, 1000, ?, ?, ?)
                                        """, usedforid, data.prp_id, import_data.lid if not all_fix else 0, data.typeid, data.wordid, data.ownerid)
                                        prp_value_id = int(cursor.execute("SELECT @@IDENTITY AS ID").fetchone()[0])
                                    if not data.is_file_content():
                                        datatype = data.datatype
                                        cursor.execute(f"""
                                        INSERT INTO {datatype} ({datatype}, valueID, part) 
                                        Values (?, ?, ?)
                                        """, data.value, prp_value_id, data.part)
                                    else:
                                        # TODO FOR FILES (BLOB OR REGULAR FILES)
                                        pass
                    db.commit()

    def _export_schema(self, export_data: SqlExportData) -> List[Answer]:
        return super()._export_schema(export_data)

    