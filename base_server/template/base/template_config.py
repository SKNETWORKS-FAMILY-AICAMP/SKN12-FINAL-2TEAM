from pydantic import BaseModel
from service.db.database_config import DatabaseConfig
from service.cache.cache_config import CacheConfig
from service.external.external_config import ExternalConfig
from service.storage.storage_config import StorageConfig
from service.search.search_config import SearchConfig
from service.vectordb.vectordb_config import VectorDbConfig
from service.llm.llm_config import LlmConfig
from service.net.net_config import NetConfig

class TemplateConfig(BaseModel):
    appId: str
    env: str
    localPath: str = ""

class ProviderConfig(BaseModel):
    provider: str
    api_key: str
    model: str

class AppConfig(BaseModel):
    databaseConfig: DatabaseConfig
    cacheConfig: CacheConfig
    externalConfig: ExternalConfig
    storageConfig: StorageConfig
    searchConfig: SearchConfig
    vectordbConfig: VectorDbConfig
    llmConfig: LlmConfig
    templateConfig: TemplateConfig