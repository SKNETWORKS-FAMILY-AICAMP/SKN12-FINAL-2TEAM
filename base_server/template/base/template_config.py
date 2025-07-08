from pydantic import BaseModel
from service.db.database_config import DatabaseConfig
from service.cache.cache_config import CacheConfig
from service.http.http_config import HttpConfig
from service.llm.llm_config import LlmConfig
from service.net.net_config import NetConfig

class TemplateConfig(BaseModel):
    appId: str
    env: str
    localPath: str = ""

class AppConfig(BaseModel):
    templateConfig: TemplateConfig
    databaseConfig: DatabaseConfig
    cacheConfig: CacheConfig
    httpConfig: HttpConfig
    llmConfig: LlmConfig
    netConfig: NetConfig