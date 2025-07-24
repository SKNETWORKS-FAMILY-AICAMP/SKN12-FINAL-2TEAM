from typing import Optional
from pydantic import BaseModel
from service.db.database_config import DatabaseConfig
from service.cache.cache_config import CacheConfig
from service.external.external_config import ExternalConfig
from service.storage.storage_config import StorageConfig
from service.search.search_config import SearchConfig
from service.vectordb.vectordb_config import VectorDbConfig
from service.llm.llm_config import LlmConfig
from service.net.net_config import NetConfig
from service.net.fastapi_config import FastApiConfig
from service.websocket.websocket_config import WebSocketConfig

class TemplateConfig(BaseModel):
    appId: str
    env: str
    localPath: str = ""
    skipAwsTests: bool = False  # AWS 서비스 테스트 스킵 여부

class ProviderConfig(BaseModel):
    provider: str
    api_key: str
    model: str

class AppConfig(BaseModel):
    templateConfig: TemplateConfig
    databaseConfig: DatabaseConfig
    cacheConfig: CacheConfig
    externalConfig: ExternalConfig
    storageConfig: StorageConfig
    searchConfig: SearchConfig
    vectordbConfig: VectorDbConfig
    llmConfig: LlmConfig
    netConfig: NetConfig
    websocketConfig: WebSocketConfig
