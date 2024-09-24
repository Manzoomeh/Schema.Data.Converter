from bclib.edge import RESTfulContext, HttpStatusCodes, DictEx, BadRequestErr
from dependency_injector.wiring import inject, Provider, Provide
from dependency_injector.errors import NoSuchProviderError
from typing import Callable, List
from providers.interface import IProvider, ProviderError
from providers.types import ProviderType
from models.schema import SchemaRepository
from models.questions import Property
from models.rkey import RkeyContext


@inject
async def import_async(context: RESTfulContext, provider_factory: Callable[[str, List[Property]], IProvider] = Provider["provider_factory"], schema_repository: SchemaRepository = Provide["schema_repo"]):
    try:
        body = context.body or DictEx()
        rkey_content = body.get("rkeyContent")
        if rkey_content is None:
            raise BadRequestErr("'rkeyContent' not found in body")
        if not isinstance(rkey_content, dict):
            raise BadRequestErr("Invalid rkeyContent datatype")
        rkey_context = RkeyContext(**rkey_content)
        schema_url = body.get("schemaUrl")
        if schema_url is None:
            raise BadRequestErr("'schemaUrl' not found in body")
        if not isinstance(schema_url, str):
            raise BadRequestErr("Invalid schemaUrl datatype")
        try:
            schema = await schema_repository.get_async(schema_url)
        except Exception as ex:
            print(repr(ex))
            raise ValueError("Invalid schemaUrl")
        source_data = body.get("sourceData")
        if source_data is None:
            raise BadRequestErr("'sourceData' not found in body")
        if not isinstance(source_data, dict):
            raise BadRequestErr("Invalid sourceData datatype in body")
        source_type = source_data.get("type")
        if not isinstance(source_type, str):
            raise BadRequestErr("Invalid sourceType datatype")
        try:
            source_provider = provider_factory(source_type.lower(), schema)
        except NoSuchProviderError as ex:
            raise BadRequestErr(f"Invalid provider type '{source_type}'")
        except Exception as ex:
            raise BadRequestErr(str(ex))
        
        dest_data = body.get("destinationData")
        if dest_data is None:
            raise BadRequestErr("'destinationData' not found in body")
        if not isinstance(dest_data, dict):
            raise BadRequestErr("Invalid destinationData type in body")
        dest_type = dest_data.get("type")
        if not isinstance(dest_type, str) or dest_type != ProviderType.SQL.value:
            raise BadRequestErr("Invalid destinationType datatype")
        try:
            dest_provider = provider_factory(dest_type.lower(), schema)
        except NoSuchProviderError as ex:
            raise BadRequestErr(f"Invalid provider type '{dest_type}'")
        except Exception as ex:
            raise BadRequestErr(str(ex))
        try:
            answers = source_provider.export_schema(source_data)
        except ProviderError as ex:
            raise BadRequestErr(message=repr(ex))
        result = await dest_provider.import_schema_async(rkey_context, answers, dest_data)
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
    
