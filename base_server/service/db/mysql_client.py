from typing import Any, Dict, List, Optional, Tuple
import asyncio
import aiomysql
from aiomysql import Pool
from .database_config import DatabaseConfig

class MySQLClient:
    def __init__(self, config: DatabaseConfig):
        self.config = config
        self.pool: Optional[Pool] = None
    
    async def init_pool(self):
        """Initialize the connection pool"""
        if self.pool is None:
            self.pool = await aiomysql.create_pool(
                host=self.config.host,
                port=self.config.port,
                user=self.config.user,
                password=self.config.password,
                db=self.config.database,
                charset=self.config.charset,
                minsize=1,
                maxsize=self.config.pool_size,
                autocommit=True
            )
    
    async def close_pool(self):
        """Close the connection pool"""
        if self.pool:
            self.pool.close()
            await self.pool.wait_closed()
            self.pool = None
    
    async def execute_stored_procedure(self, procedure_name: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a stored procedure and return results"""
        await self._ensure_connection()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.callproc(procedure_name, params)
                    
                    # 모든 result set을 하나로 합쳐서 반환
                    all_results = []
                    while True:
                        result = await cursor.fetchall()
                        if result:
                            all_results.extend(result)
                        
                        # Check if there are more result sets
                        if not cursor.nextset():
                            break
                    
                    return all_results
        except Exception as e:
            # 연결 문제일 경우 재연결 시도
            if self._is_connection_error(e):
                await self._reconnect()
                async with self.pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.callproc(procedure_name, params)
                        
                        # 모든 result set을 하나로 합쳐서 반환
                        all_results = []
                        while True:
                            result = await cursor.fetchall()
                            if result:
                                all_results.extend(result)
                            
                            # Check if there are more result sets
                            if not cursor.nextset():
                                break
                        
                        return all_results
            else:
                raise
    
    async def execute_query(self, query: str, params: Tuple = ()) -> List[Dict[str, Any]]:
        """Execute a SELECT query and return results"""
        await self._ensure_connection()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor(aiomysql.DictCursor) as cursor:
                    await cursor.execute(query, params)
                    results = await cursor.fetchall()
                    return results if results else []
        except Exception as e:
            if self._is_connection_error(e):
                await self._reconnect()
                async with self.pool.acquire() as conn:
                    async with conn.cursor(aiomysql.DictCursor) as cursor:
                        await cursor.execute(query, params)
                        results = await cursor.fetchall()
                        return results if results else []
            else:
                raise
    
    async def execute_non_query(self, query: str, params: Tuple = ()) -> int:
        """Execute INSERT, UPDATE, DELETE and return affected rows"""
        await self._ensure_connection()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    affected_rows = await cursor.execute(query, params)
                    return affected_rows
        except Exception as e:
            if self._is_connection_error(e):
                await self._reconnect()
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        affected_rows = await cursor.execute(query, params)
                        return affected_rows
            else:
                raise
    
    async def get_last_insert_id(self) -> int:
        """Get the last inserted ID"""
        await self._ensure_connection()
        
        try:
            async with self.pool.acquire() as conn:
                async with conn.cursor() as cursor:
                    await cursor.execute("SELECT LAST_INSERT_ID()")
                    result = await cursor.fetchone()
                    return result[0] if result else 0
        except Exception as e:
            if self._is_connection_error(e):
                await self._reconnect()
                async with self.pool.acquire() as conn:
                    async with conn.cursor() as cursor:
                        await cursor.execute("SELECT LAST_INSERT_ID()")
                        result = await cursor.fetchone()
                        return result[0] if result else 0
            else:
                raise
    
    async def _ensure_connection(self):
        """연결 풀이 존재하고 유효한지 확인"""
        if not self.pool or self.pool.closed:
            await self.init_pool()
    
    async def _reconnect(self):
        """연결 풀 재생성"""
        if self.pool:
            try:
                self.pool.close()
                await self.pool.wait_closed()
            except:
                pass
        self.pool = None
        await self.init_pool()
    
    def _is_connection_error(self, exception) -> bool:
        """연결 관련 에러인지 확인"""
        error_messages = [
            "MySQL server has gone away",
            "Lost connection to MySQL server",
            "Connection reset by peer",
            "Broken pipe",
            "Can't connect to MySQL server"
        ]
        error_str = str(exception).lower()
        return any(msg.lower() in error_str for msg in error_messages)
    
    async def get_connection(self):
        """Get a connection from the pool for transaction use"""
        await self._ensure_connection()
        return await self.pool.acquire()