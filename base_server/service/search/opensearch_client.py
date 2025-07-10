import asyncio
import time
import random
from opensearchpy import AsyncOpenSearch, ConnectionError, TransportError
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from service.core.logger import Logger
from .search_client import ISearchClient

class ConnectionState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"

@dataclass
class SearchMetrics:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_search_time: float = 0.0
    total_index_time: float = 0.0
    documents_indexed: int = 0
    documents_searched: int = 0
    last_operation_time: Optional[float] = None
    connection_failures: int = 0
    timeout_errors: int = 0
    index_errors: int = 0
    search_errors: int = 0

class OpenSearchClient(ISearchClient):
    """OpenSearch 클라이언트 - 연결 관리, 재시도, 메트릭 포함"""
    
    def __init__(self, config):
        self.config = config
        self._client = None
        self.metrics = SearchMetrics()
        self.connection_state = ConnectionState.HEALTHY
        self._last_health_check = 0
        self._max_retries = getattr(config, 'max_retries', 3)
        self._retry_delay_base = 1.0
        self._connection_pool_kwargs = {
            'maxsize': 20,
            'block': True
        }
    
    async def _get_client(self):
        """OpenSearch 클라이언트 가져오기 (Enhanced connection management)"""
        for attempt in range(self._max_retries):
            try:
                if self._client is None:
                    client_kwargs = {
                        'hosts': self.config.hosts,
                        'timeout': self.config.timeout,
                        'max_retries': self._max_retries,
                        'retry_on_timeout': getattr(self.config, 'retry_on_timeout', True),
                        'use_ssl': getattr(self.config, 'use_ssl', True),
                        'verify_certs': getattr(self.config, 'verify_certs', False),
                        'connection_class': None,  # AsyncOpenSearch default
                        'pool_maxsize': 20,
                        'pool_block': True
                    }
                    
                    # 인증 설정
                    if self.config.username and self.config.password:
                        client_kwargs['http_auth'] = (self.config.username, self.config.password)
                    
                    # AWS 설정
                    if self.config.aws_access_key_id and self.config.aws_secret_access_key:
                        from opensearchpy import RequestsHttpConnection
                        from requests_aws4auth import AWS4Auth
                        
                        auth = AWS4Auth(
                            self.config.aws_access_key_id,
                            self.config.aws_secret_access_key,
                            self.config.aws_region,
                            'es'
                        )
                        client_kwargs['http_auth'] = auth
                        client_kwargs['connection_class'] = RequestsHttpConnection
                    
                    # CA 인증서
                    if self.config.ca_certs:
                        client_kwargs['ca_certs'] = self.config.ca_certs
                    
                    self._client = AsyncOpenSearch(**client_kwargs)
                    
                    # 연결 테스트
                    await self._test_connection()
                    self.connection_state = ConnectionState.HEALTHY
                    Logger.info(f"OpenSearch client connected to {self.config.hosts}")
                
                return self._client
                
            except ConnectionError as e:
                self.metrics.connection_failures += 1
                self.connection_state = ConnectionState.FAILED
                Logger.warn(f"OpenSearch connection failed (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                self.metrics.connection_failures += 1
                self.connection_state = ConnectionState.DEGRADED
                Logger.warn(f"OpenSearch client initialization failed (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.connection_state = ConnectionState.FAILED
        raise ConnectionError(f"Failed to connect to OpenSearch after {self._max_retries} attempts")
    
    async def _test_connection(self):
        """OpenSearch 연결 테스트"""
        if self._client:
            await self._client.ping()
            Logger.debug("OpenSearch connection test successful")
    
    async def create_index(self, index: str, mappings: Optional[Dict] = None, settings: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """인덱스 생성"""
        try:
            client = await self._get_client()
            
            body = {}
            if mappings:
                body['mappings'] = mappings
            if settings:
                body['settings'] = settings
            
            response = await client.indices.create(
                index=index,
                body=body,
                **kwargs
            )
            
            Logger.info(f"OpenSearch index created: {index}")
            return {
                "success": True,
                "index": index,
                "response": response
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch create_index failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_index(self, index: str, **kwargs) -> Dict[str, Any]:
        """인덱스 삭제"""
        try:
            client = await self._get_client()
            
            response = await client.indices.delete(
                index=index,
                **kwargs
            )
            
            Logger.info(f"OpenSearch index deleted: {index}")
            return {
                "success": True,
                "index": index,
                "response": response
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch delete_index failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def index_exists(self, index: str, **kwargs) -> Dict[str, Any]:
        """인덱스 존재 확인 (향상된 에러 처리)"""
        start_time = time.time()
        self.metrics.total_operations += 1
        self.metrics.last_operation_time = start_time
        
        for attempt in range(self._max_retries):
            try:
                client = await self._get_client()
                
                exists = await client.indices.exists(
                    index=index,
                    **kwargs
                )
                
                # 성공 메트릭
                self.metrics.successful_operations += 1
                operation_time = time.time() - start_time
                
                return {
                    "success": True,
                    "index": index,
                    "exists": exists,
                    "operation_time": operation_time,
                    "attempt": attempt + 1
                }
                
            except ConnectionError as e:
                self.metrics.connection_failures += 1
                Logger.warn(f"OpenSearch connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except TransportError as e:
                self.metrics.timeout_errors += 1
                Logger.warn(f"OpenSearch transport error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                Logger.warn(f"OpenSearch index_exists error (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.metrics.failed_operations += 1
        total_time = time.time() - start_time
        Logger.error(f"OpenSearch index_exists failed after {self._max_retries} attempts: {index} (total: {total_time:.3f}s)")
        return {
            "success": False,
            "error": f"Failed after {self._max_retries} attempts",
            "index": index,
            "total_time": total_time,
            "attempts": self._max_retries
        }
    
    async def index_document(self, index: str, document: Dict[str, Any], doc_id: Optional[str] = None, **kwargs) -> Dict[str, Any]:
        """문서 인덱싱 (향상된 에러 처리 및 메트릭)"""
        start_time = time.time()
        self.metrics.total_operations += 1
        self.metrics.last_operation_time = start_time
        
        for attempt in range(self._max_retries):
            try:
                client = await self._get_client()
                
                index_kwargs = {
                    'index': index,
                    'body': document,
                    **kwargs
                }
                
                if doc_id:
                    index_kwargs['id'] = doc_id
                
                response = await client.index(**index_kwargs)
                
                # 성공 메트릭
                index_time = time.time() - start_time
                self.metrics.successful_operations += 1
                self.metrics.total_index_time += index_time
                self.metrics.documents_indexed += 1
                
                Logger.debug(f"OpenSearch document indexed: {index}/{response.get('_id')} ({index_time:.3f}s)")
                return {
                    "success": True,
                    "index": index,
                    "doc_id": response.get('_id'),
                    "index_time": index_time,
                    "attempt": attempt + 1,
                    "response": response
                }
                
            except ConnectionError as e:
                self.metrics.connection_failures += 1
                Logger.warn(f"OpenSearch index connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except TransportError as e:
                self.metrics.index_errors += 1
                Logger.warn(f"OpenSearch index transport error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                self.metrics.index_errors += 1
                Logger.warn(f"OpenSearch index error (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.metrics.failed_operations += 1
        total_time = time.time() - start_time
        Logger.error(f"OpenSearch index_document failed after {self._max_retries} attempts: {index} (total: {total_time:.3f}s)")
        return {
            "success": False,
            "error": f"Index failed after {self._max_retries} attempts",
            "index": index,
            "total_time": total_time,
            "attempts": self._max_retries
        }
    
    async def get_document(self, index: str, doc_id: str, **kwargs) -> Dict[str, Any]:
        """문서 조회"""
        try:
            client = await self._get_client()
            
            response = await client.get(
                index=index,
                id=doc_id,
                **kwargs
            )
            
            return {
                "success": True,
                "index": index,
                "doc_id": doc_id,
                "document": response.get('_source'),
                "response": response
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch get_document failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def update_document(self, index: str, doc_id: str, document: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """문서 업데이트"""
        try:
            client = await self._get_client()
            
            response = await client.update(
                index=index,
                id=doc_id,
                body={'doc': document},
                **kwargs
            )
            
            Logger.debug(f"OpenSearch document updated: {index}/{doc_id}")
            return {
                "success": True,
                "index": index,
                "doc_id": doc_id,
                "response": response
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch update_document failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def delete_document(self, index: str, doc_id: str, **kwargs) -> Dict[str, Any]:
        """문서 삭제"""
        try:
            client = await self._get_client()
            
            response = await client.delete(
                index=index,
                id=doc_id,
                **kwargs
            )
            
            Logger.debug(f"OpenSearch document deleted: {index}/{doc_id}")
            return {
                "success": True,
                "index": index,
                "doc_id": doc_id,
                "response": response
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch delete_document failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def search(self, index: str, query: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """검색 (향상된 에러 처리 및 메트릭)"""
        start_time = time.time()
        self.metrics.total_operations += 1
        self.metrics.last_operation_time = start_time
        
        for attempt in range(self._max_retries):
            try:
                client = await self._get_client()
                
                response = await client.search(
                    index=index,
                    body=query,
                    **kwargs
                )
                
                hits = response.get('hits', {})
                documents = [hit.get('_source') for hit in hits.get('hits', [])]
                total_hits = hits.get('total', {}).get('value', 0)
                
                # 성공 메트릭
                search_time = time.time() - start_time
                self.metrics.successful_operations += 1
                self.metrics.total_search_time += search_time
                self.metrics.documents_searched += total_hits
                
                Logger.debug(f"OpenSearch search: {index} - {total_hits} results ({search_time:.3f}s)")
                return {
                    "success": True,
                    "index": index,
                    "total": total_hits,
                    "documents": documents,
                    "search_time": search_time,
                    "attempt": attempt + 1,
                    "response": response
                }
                
            except ConnectionError as e:
                self.metrics.connection_failures += 1
                Logger.warn(f"OpenSearch search connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except TransportError as e:
                self.metrics.search_errors += 1
                Logger.warn(f"OpenSearch search transport error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                self.metrics.search_errors += 1
                Logger.warn(f"OpenSearch search error (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.metrics.failed_operations += 1
        total_time = time.time() - start_time
        Logger.error(f"OpenSearch search failed after {self._max_retries} attempts: {index} (total: {total_time:.3f}s)")
        return {
            "success": False,
            "error": f"Search failed after {self._max_retries} attempts",
            "index": index,
            "total_time": total_time,
            "attempts": self._max_retries
        }
    
    async def bulk_index(self, operations: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """벌크 인덱싱"""
        try:
            client = await self._get_client()
            
            response = await client.bulk(
                body=operations,
                **kwargs
            )
            
            errors = response.get('errors', False)
            items = response.get('items', [])
            
            Logger.info(f"OpenSearch bulk operation: {len(items)} items, errors: {errors}")
            return {
                "success": not errors,
                "items_count": len(items),
                "has_errors": errors,
                "response": response
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch bulk_index failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def scroll_search(self, index: str, query: Dict[str, Any], scroll_time: str = "5m", **kwargs) -> Dict[str, Any]:
        """스크롤 검색"""
        try:
            client = await self._get_client()
            
            # 초기 검색
            response = await client.search(
                index=index,
                body=query,
                scroll=scroll_time,
                **kwargs
            )
            
            scroll_id = response.get('_scroll_id')
            hits = response.get('hits', {})
            documents = [hit.get('_source') for hit in hits.get('hits', [])]
            
            Logger.debug(f"OpenSearch scroll_search started: {index} - scroll_id: {scroll_id[:10]}...")
            return {
                "success": True,
                "index": index,
                "scroll_id": scroll_id,
                "total": hits.get('total', {}).get('value', 0),
                "documents": documents,
                "response": response
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch scroll_search failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # === 모니터링 및 관리 메소드들 ===
    
    async def health_check(self) -> Dict[str, Any]:
        """OpenSearch 연결 상태 확인"""
        start_time = time.time()
        
        try:
            client = await self._get_client()
            
            # Cluster health 확인
            health_response = await client.cluster.health()
            
            # Ping 테스트
            ping_result = await client.ping()
            
            response_time = time.time() - start_time
            self.connection_state = ConnectionState.HEALTHY
            self._last_health_check = time.time()
            
            return {
                "healthy": True,
                "response_time": response_time,
                "connection_state": self.connection_state.value,
                "cluster_status": health_response.get('status', 'unknown'),
                "cluster_name": health_response.get('cluster_name', 'unknown'),
                "nodes": health_response.get('number_of_nodes', 0),
                "ping_result": ping_result,
                "hosts": self.config.hosts,
                "metrics": self.get_metrics()
            }
            
        except ConnectionError as e:
            self.connection_state = ConnectionState.FAILED
            return {
                "healthy": False,
                "error": f"Connection error: {e}",
                "error_type": "connection",
                "connection_state": self.connection_state.value,
                "hosts": self.config.hosts,
                "metrics": self.get_metrics()
            }
        except Exception as e:
            self.connection_state = ConnectionState.DEGRADED
            return {
                "healthy": False,
                "error": str(e),
                "error_type": "unknown",
                "connection_state": self.connection_state.value,
                "hosts": self.config.hosts,
                "metrics": self.get_metrics()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """OpenSearch 클라이언트 메트릭 조회"""
        avg_search_time = 0.0
        avg_index_time = 0.0
        success_rate = 0.0
        
        if self.metrics.successful_operations > 0:
            if self.metrics.total_search_time > 0:
                # 검색 작업 추정
                search_operations = max(1, self.metrics.successful_operations // 2)
                avg_search_time = self.metrics.total_search_time / search_operations
            
            if self.metrics.total_index_time > 0:
                index_operations = max(1, self.metrics.successful_operations // 2)
                avg_index_time = self.metrics.total_index_time / index_operations
        
        if self.metrics.total_operations > 0:
            success_rate = self.metrics.successful_operations / self.metrics.total_operations
        
        return {
            "total_operations": self.metrics.total_operations,
            "successful_operations": self.metrics.successful_operations,
            "failed_operations": self.metrics.failed_operations,
            "success_rate": success_rate,
            "average_search_time": avg_search_time,
            "average_index_time": avg_index_time,
            "documents_indexed": self.metrics.documents_indexed,
            "documents_searched": self.metrics.documents_searched,
            "connection_failures": self.metrics.connection_failures,
            "timeout_errors": self.metrics.timeout_errors,
            "index_errors": self.metrics.index_errors,
            "search_errors": self.metrics.search_errors,
            "last_operation_time": self.metrics.last_operation_time,
            "connection_state": self.connection_state.value,
            "last_health_check": self._last_health_check
        }
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = SearchMetrics()
        Logger.info("OpenSearch client metrics reset")
    
    async def close(self):
        """클라이언트 종료"""
        if self._client:
            try:
                await self._client.close()
            except:
                pass
            self._client = None
            Logger.info("OpenSearch client closed")
            
            # 최종 메트릭 로깅
            final_metrics = self.get_metrics()
            Logger.info(f"Final OpenSearch metrics: {final_metrics}")