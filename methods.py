from bclib.edge import RESTfulContext, HttpStatusCodes, DictEx, BadRequestErr, UnauthorizedErr
from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector.errors import NoSuchProviderError
from typing import Callable, List, Union, Dict
from providers.interface import IProvider, ProviderError
from providers.types import ProviderType
from models.schema import SchemaRepository
from models.questions import Property

async def check_rkey_async(context: RESTfulContext):
    rest_api = context.open_restful_connection("check_rkey")
    with rest_api:
        checked = await rest_api.get_async(f"/{context.url_segments.rkey}")
    if not isinstance(checked, dict):
        checked = dict()
    status = bool(checked.get("checked") == True)
    if status:
        context.check_rkey = DictEx(checked)
    else:
        raise UnauthorizedErr(data={
            "errorid": 1,
            "message": "Invalid rkey!"
        })

@inject
async def import_async(context: RESTfulContext, provider_factory: Callable[[str, List[Property]], IProvider] = Provider["provider_factory"], schema_repository: SchemaRepository = Provide["schema_repo"]):
    try:
        body = context.body or DictEx()
        
        schema_url = body.get("schemaUrl")
        if schema_url is None:
            raise BadRequestErr("'schemaUrl' not found in body")
        if not isinstance(schema_url, str):
            raise BadRequestErr("Invalid schemaUrl datatype")
        try:
            url_segments = context.url_segments
            rkey = url_segments.rkey
            culture = url_segments.culture
            schema = await schema_repository.get_async(schema_url, rkey, culture)
        except Exception as ex:
            print(repr(ex))
            raise ValueError("Invalid schemaUrl")
        
        source_data = body.get("source")
        if source_data is None:
            raise BadRequestErr("'source' not found in body")
        if not isinstance(source_data, dict):
            raise BadRequestErr("Invalid source datatype in body")
        source_type = source_data.get("type")
        if not isinstance(source_type, str):
            raise BadRequestErr("Invalid sourceType datatype")
        try:
            source_provider = provider_factory(source_type.lower(), schema)
        except NoSuchProviderError as ex:
            raise BadRequestErr(f"Invalid provider type '{source_type}'")
        except Exception as ex:
            raise BadRequestErr(str(ex))
        
        destinations = body.get("destinations")
        if destinations is None:
            raise BadRequestErr("'destinations' not found in body")
        if not isinstance(destinations, list):
            raise BadRequestErr("Invalid destinations type in body")
        destination_obejcts: Dict[str, Dict[str, Union[IProvider, Dict]]] = dict()
        for index, dest_data in enumerate(destinations):
            if not isinstance(dest_data, dict):
                raise Exception(f"Invalid destinationData at index={index}")
            name = dest_data.get("name", f"Destination_{index}")
            if not isinstance(name, str):
                raise Exception(f"Invalid destination name type at index={index}")
            if name in destination_obejcts:
                raise Exception(f"Repetetive name={name}")
            dest_type = dest_data.get("type")
            if not isinstance(dest_type, str):
                raise BadRequestErr("Invalid destinationType datatype")
            try:
                dest_provider = provider_factory(dest_type.lower(), schema)
            except NoSuchProviderError as ex:
                raise BadRequestErr(f"Invalid provider type '{dest_type}'")
            except Exception as ex:
                raise BadRequestErr(str(ex))
            destination_obejcts[name] = {
                "obj": dest_provider,
                "data": dest_data
            }
        try:
            answers = source_provider.export_schema(source_data)
        except ProviderError as ex:
            raise BadRequestErr(message=repr(ex))
        result = list()
        for name, dest_obj in destination_obejcts.items():
            dest_provider = dest_obj["obj"]
            dest_data = dest_obj["data"]
            resp = await dest_provider.import_schema_async(answers, dest_data) or {
                "errorid": 5,
                "message": "successful"
            }
            result.append({
                "name": name,
                "response": resp
            })
    except BadRequestErr as ex:
        print(str(ex))
        context.status_code = HttpStatusCodes.BAD_REQUEST
        result = {
            "errorid": 4
        }
    except Exception as ex:
        print(str(ex))
        context.status_code = HttpStatusCodes.INTERNAL_SERVER_ERROR
        result = {
            "errorid": 0,
            "message": "Server Error!"
        }
    return result
    
