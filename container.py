from dependency_injector.containers import DeclarativeContainer
from dependency_injector.providers import Configuration, FactoryAggregate, Factory, Singleton
from providers import ProviderType, IProvider, ExcelProvider, SqlProvider, ApiProvider
from models.schema import SchemaRepository


class Container(DeclarativeContainer):
    config = Configuration()
    
    provider_factory = FactoryAggregate(
        {
            ProviderType.EXCEL.value.lower(): Factory(
                ExcelProvider
            ),
            ProviderType.SQL.value.lower(): Factory(
                SqlProvider
            ),
            ProviderType.API.value.lower(): Factory(
                ApiProvider
            ),
        }
    )
    
    schema_repo = Singleton(
        SchemaRepository
    )
