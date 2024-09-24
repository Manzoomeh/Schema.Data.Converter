from pydantic import BaseModel

class RkeyContext:
    rkey: str
    userid: int
    ownerid: int
    dmnid: int
