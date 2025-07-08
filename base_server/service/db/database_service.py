from typing import Any, Dict, List, Optional, Tuple
from .database_config import DatabaseConfig
from .mysql_client import MySQLClient
from service.core.logger import Logger

class DatabaseService:
    def __init__(self, global_config: DatabaseConfig):
        self.global_config = global_config
        self.global_client: Optional[MySQLClient] = None
        self.shard_clients: Dict[int, MySQLClient] = {}  # shard_id -> MySQLClient
        self.shard_configs: Dict[int, DatabaseConfig] = {}  # shard_id -> DatabaseConfig
        
    async def init_service(self):
        """Initialize database service"""
        # 글로벌 DB 초기화
        if self.global_config.type == "mysql":
            self.global_client = MySQLClient(self.global_config)
            await self.global_client.init_pool()
            Logger.info("Global database initialized")
        else:
            raise ValueError(f"Unsupported database type: {self.global_config.type}")
        
        # 샤드 설정 로드 및 초기화
        await self.load_shard_configs()
        await self.init_shard_connections()
    
    async def close_service(self):
        """Close database service"""
        # 글로벌 DB 종료
        if self.global_client:
            await self.global_client.close_pool()
            Logger.info("Global database closed")
        
        # 모든 샤드 DB 종료
        for shard_id, shard_client in self.shard_clients.items():
            await shard_client.close_pool()
            Logger.info(f"Shard {shard_id} database closed")
        
        self.shard_clients.clear()
        self.shard_configs.clear()
    
    async def load_shard_configs(self):
        """글로벌 DB에서 샤드 설정 정보 로드"""
        try:
            query = """
            SELECT shard_id, host, port, database_name, username, password, status
            FROM table_shard_config 
            WHERE status = 'active'
            ORDER BY shard_id
            """
            shard_rows = await self.global_client.execute_query(query)
            
            for row in shard_rows:
                shard_id = row['shard_id']
                shard_config = DatabaseConfig(
                    type="mysql",
                    host=row['host'],
                    port=row['port'],
                    database=row['database_name'],
                    user=row['username'],
                    password=row['password']
                )
                self.shard_configs[shard_id] = shard_config
                Logger.info(f"Loaded shard config for shard_id: {shard_id}")
                
        except Exception as e:
            Logger.error(f"Failed to load shard configs: {e}")
            # 샤드 설정이 없어도 글로벌 DB는 사용 가능하도록
    
    async def init_shard_connections(self):
        """샤드 DB 연결 초기화"""
        for shard_id, config in self.shard_configs.items():
            try:
                shard_client = MySQLClient(config)
                await shard_client.init_pool()
                self.shard_clients[shard_id] = shard_client
                Logger.info(f"Shard {shard_id} database initialized")
            except Exception as e:
                Logger.error(f"Failed to initialize shard {shard_id}: {e}")
    
    def get_global_client(self) -> MySQLClient:
        """글로벌 DB 클라이언트 반환"""
        if not self.global_client:
            raise RuntimeError("Global database not initialized")
        return self.global_client
    
    def get_shard_client(self, shard_id: int) -> Optional[MySQLClient]:
        """샤드 DB 클라이언트 반환"""
        return self.shard_clients.get(shard_id)
    
    def get_client_by_session(self, client_session) -> MySQLClient:
        """세션 정보를 기반으로 적절한 DB 클라이언트 반환"""
        if not client_session or not hasattr(client_session, 'session') or not client_session.session:
            # 세션이 없으면 글로벌 DB 사용 (로그인, 회원가입 등)
            return self.get_global_client()
        
        shard_id = getattr(client_session.session, 'shard_id', None)
        if shard_id and shard_id in self.shard_clients:
            return self.shard_clients[shard_id]
        else:
            # 샤드 정보가 없거나 해당 샤드가 없으면 글로벌 DB 사용
            return self.get_global_client()
    
    # === 글로벌 DB 전용 메서드 ===
    async def call_global_procedure(self, procedure_name: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """글로벌 DB 스토어드 프로시저 호출"""
        return await self.global_client.execute_stored_procedure(procedure_name, params)
    
    async def execute_global_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """글로벌 DB 쿼리 실행"""
        return await self.global_client.execute_query(query, params)
    
    # === 샤드 DB 전용 메서드 ===
    async def call_shard_procedure(self, shard_id: int, procedure_name: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """특정 샤드 DB 스토어드 프로시저 호출"""
        shard_client = self.get_shard_client(shard_id)
        if not shard_client:
            raise RuntimeError(f"Shard {shard_id} not available")
        return await shard_client.execute_stored_procedure(procedure_name, params)
    
    async def execute_shard_query(self, shard_id: int, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """특정 샤드 DB 쿼리 실행"""
        shard_client = self.get_shard_client(shard_id)
        if not shard_client:
            raise RuntimeError(f"Shard {shard_id} not available")
        return await shard_client.execute_query(query, params)
    
    # === 세션 기반 메서드 (자동 라우팅) ===
    async def call_procedure_by_session(self, client_session, procedure_name: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """세션 정보를 기반으로 적절한 DB에 스토어드 프로시저 호출"""
        client = self.get_client_by_session(client_session)
        return await client.execute_stored_procedure(procedure_name, params)
    
    async def execute_query_by_session(self, client_session, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """세션 정보를 기반으로 적절한 DB에 쿼리 실행"""
        client = self.get_client_by_session(client_session)
        return await client.execute_query(query, params)
    
    # === 호환성을 위한 기존 메서드 (글로벌 DB로 라우팅) ===
    async def call_stored_procedure(self, procedure_name: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """기존 호환성을 위한 메서드 - 글로벌 DB 사용"""
        return await self.call_global_procedure(procedure_name, params)
    
    async def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """기존 호환성을 위한 메서드 - 글로벌 DB 사용"""
        return await self.execute_global_query(query, params)
    
    async def execute_non_query(self, query: str, params: Tuple = ()) -> int:
        """기존 호환성을 위한 메서드 - 글로벌 DB 사용"""
        return await self.global_client.execute_non_query(query, params)
    
    async def get_last_insert_id(self) -> int:
        """기존 호환성을 위한 메서드 - 글로벌 DB 사용"""
        return await self.global_client.get_last_insert_id()