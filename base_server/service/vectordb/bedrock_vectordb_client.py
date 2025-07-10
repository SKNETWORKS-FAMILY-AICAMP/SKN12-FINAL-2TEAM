import asyncio
import json
import time
import random
import aioboto3
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum
from botocore.exceptions import ClientError, NoCredentialsError, EndpointConnectionError
from service.core.logger import Logger
from .vectordb_client import IVectorDbClient

class ConnectionState(Enum):
    HEALTHY = "healthy"
    DEGRADED = "degraded"
    FAILED = "failed"

@dataclass
class VectorDbMetrics:
    total_operations: int = 0
    successful_operations: int = 0
    failed_operations: int = 0
    total_embedding_time: float = 0.0
    total_search_time: float = 0.0
    total_generation_time: float = 0.0
    texts_embedded: int = 0
    searches_performed: int = 0
    texts_generated: int = 0
    last_operation_time: Optional[float] = None
    connection_failures: int = 0
    credential_errors: int = 0
    timeout_errors: int = 0
    model_errors: int = 0

class BedrockVectorDbClient(IVectorDbClient):
    """AWS Bedrock VectorDB 클라이언트 - 연결 관리, 재시도, 메트릭 포함"""
    
    def __init__(self, config):
        self.config = config
        self._session = None
        self._bedrock_client = None
        self._bedrock_runtime_client = None
        self._knowledge_base_client = None
        self.metrics = VectorDbMetrics()
        self.connection_state = ConnectionState.HEALTHY
        self._last_health_check = 0
        self._max_retries = getattr(config, 'max_retries', 3)
        self._retry_delay_base = 1.0
    
    async def _get_bedrock_client(self):
        """Bedrock 클라이언트 가져오기 (Enhanced connection management)"""
        for attempt in range(self._max_retries):
            try:
                if self._bedrock_client is None:
                    self._session = aioboto3.Session(
                        aws_access_key_id=self.config.aws_access_key_id,
                        aws_secret_access_key=self.config.aws_secret_access_key,
                        aws_session_token=getattr(self.config, 'aws_session_token', None),
                        region_name=self.config.aws_region
                    )
                    self._bedrock_client = self._session.client(
                        'bedrock',
                        config={
                            'retries': {'max_attempts': 3, 'mode': 'adaptive'},
                            'max_pool_connections': 50
                        }
                    )
                    
                    # 연결 테스트
                    await self._test_connection()
                    self.connection_state = ConnectionState.HEALTHY
                    Logger.info(f"Bedrock client connected to region: {self.config.aws_region}")
                
                return self._bedrock_client
                
            except NoCredentialsError as e:
                self.metrics.credential_errors += 1
                self.connection_state = ConnectionState.FAILED
                Logger.error(f"Bedrock credentials error: {e}")
                raise
                
            except EndpointConnectionError as e:
                self.metrics.connection_failures += 1
                self.connection_state = ConnectionState.FAILED
                Logger.warn(f"Bedrock connection failed (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                self.metrics.connection_failures += 1
                self.connection_state = ConnectionState.DEGRADED
                Logger.warn(f"Bedrock client initialization failed (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.connection_state = ConnectionState.FAILED
        raise ConnectionError(f"Failed to connect to Bedrock after {self._max_retries} attempts")
    
    async def _get_bedrock_runtime_client(self):
        """Bedrock Runtime 클라이언트 가져오기 (Enhanced connection management)"""
        for attempt in range(self._max_retries):
            try:
                if self._bedrock_runtime_client is None:
                    if self._session is None:
                        await self._get_bedrock_client()
                    self._bedrock_runtime_client = self._session.client(
                        'bedrock-runtime',
                        config={
                            'retries': {'max_attempts': 3, 'mode': 'adaptive'},
                            'max_pool_connections': 50
                        }
                    )
                    Logger.info(f"Bedrock Runtime client initialized for region: {self.config.aws_region}")
                
                return self._bedrock_runtime_client
                
            except Exception as e:
                self.metrics.connection_failures += 1
                Logger.warn(f"Bedrock Runtime client initialization failed (attempt {attempt + 1}/{self._max_retries}): {e}")
                
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)
                else:
                    raise
        
        raise ConnectionError(f"Failed to initialize Bedrock Runtime client after {self._max_retries} attempts")
    
    async def _get_knowledge_base_client(self):
        """Bedrock Knowledge Base 클라이언트 가져오기 (Enhanced connection management)"""
        for attempt in range(self._max_retries):
            try:
                if self._knowledge_base_client is None:
                    if self._session is None:
                        await self._get_bedrock_client()
                    self._knowledge_base_client = self._session.client(
                        'bedrock-agent-runtime',
                        config={
                            'retries': {'max_attempts': 3, 'mode': 'adaptive'},
                            'max_pool_connections': 50
                        }
                    )
                    Logger.info(f"Bedrock Knowledge Base client initialized for region: {self.config.aws_region}")
                
                return self._knowledge_base_client
                
            except Exception as e:
                self.metrics.connection_failures += 1
                Logger.warn(f"Bedrock Knowledge Base client initialization failed (attempt {attempt + 1}/{self._max_retries}): {e}")
                
                if attempt < self._max_retries - 1:
                    delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                    await asyncio.sleep(delay)
                else:
                    raise
        
        raise ConnectionError(f"Failed to initialize Bedrock Knowledge Base client after {self._max_retries} attempts")
    
    async def _test_connection(self):
        """Bedrock 연결 테스트"""
        if self._bedrock_client:
            async with self._bedrock_client as client:
                await client.list_foundation_models()
            Logger.debug("Bedrock connection test successful")
    
    async def embed_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """텍스트를 벡터로 임베딩 (향상된 에러 처리 및 메트릭)"""
        start_time = time.time()
        self.metrics.total_operations += 1
        self.metrics.last_operation_time = start_time
        
        for attempt in range(self._max_retries):
            try:
                client = await self._get_bedrock_runtime_client()
                
                model_id = kwargs.get('model_id', self.config.embedding_model)
                
                body = {
                    "inputText": text
                }
                
                async with client as bedrock:
                    response = await bedrock.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body),
                        contentType='application/json',
                        accept='application/json'
                    )
                
                response_body = json.loads(await response['body'].read())
                embedding = response_body.get('embedding', [])
                
                # 성공 메트릭
                embedding_time = time.time() - start_time
                self.metrics.successful_operations += 1
                self.metrics.total_embedding_time += embedding_time
                self.metrics.texts_embedded += 1
                
                Logger.debug(f"Bedrock embed_text success: {len(embedding)} dimensions ({embedding_time:.3f}s)")
                return {
                    "success": True,
                    "text": text,
                    "embedding": embedding,
                    "model": model_id,
                    "embedding_time": embedding_time,
                    "attempt": attempt + 1
                }
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                self.metrics.model_errors += 1
                Logger.warn(f"Bedrock embed_text client error (attempt {attempt + 1}/{self._max_retries}): {error_code} - {e}")
                
                if error_code in ['ValidationException', 'AccessDeniedException']:
                    # 재시도해도 해결되지 않는 오류들
                    break
                    
            except EndpointConnectionError as e:
                self.metrics.connection_failures += 1
                Logger.warn(f"Bedrock connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                Logger.warn(f"Bedrock embed_text error (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.metrics.failed_operations += 1
        total_time = time.time() - start_time
        Logger.error(f"Bedrock embed_text failed after {self._max_retries} attempts (total: {total_time:.3f}s)")
        return {
            "success": False,
            "error": f"Embedding failed after {self._max_retries} attempts",
            "total_time": total_time,
            "attempts": self._max_retries
        }
    
    async def embed_texts(self, texts: List[str], **kwargs) -> Dict[str, Any]:
        """여러 텍스트를 벡터로 임베딩"""
        try:
            results = []
            for text in texts:
                result = await self.embed_text(text, **kwargs)
                if result["success"]:
                    results.append(result["embedding"])
                else:
                    results.append(None)
            
            Logger.debug(f"Bedrock embed_texts success: {len(texts)} texts")
            return {
                "success": True,
                "texts": texts,
                "embeddings": results
            }
            
        except Exception as e:
            Logger.error(f"Bedrock embed_texts failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def similarity_search(self, query: str, top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """유사도 검색 (Knowledge Base 사용) - 향상된 에러 처리 및 메트릭"""
        start_time = time.time()
        self.metrics.total_operations += 1
        self.metrics.last_operation_time = start_time
        
        for attempt in range(self._max_retries):
            try:
                if not self.config.knowledge_base_id:
                    raise ValueError("Knowledge Base ID not configured")
                
                client = await self._get_knowledge_base_client()
                
                async with client as kb_client:
                    response = await kb_client.retrieve(
                        knowledgeBaseId=self.config.knowledge_base_id,
                        retrievalQuery={
                            'text': query
                        },
                        retrievalConfiguration={
                            'vectorSearchConfiguration': {
                                'numberOfResults': top_k
                            }
                        }
                    )
                
                results = []
                if 'retrievalResults' in response:
                    for result in response['retrievalResults']:
                        results.append({
                            'content': result.get('content', {}).get('text', ''),
                            'score': result.get('score', 0.0),
                            'metadata': result.get('metadata', {}),
                            'location': result.get('location', {})
                        })
                
                # 성공 메트릭
                search_time = time.time() - start_time
                self.metrics.successful_operations += 1
                self.metrics.total_search_time += search_time
                self.metrics.searches_performed += 1
                
                Logger.debug(f"Bedrock similarity_search success: {len(results)} results ({search_time:.3f}s)")
                return {
                    "success": True,
                    "query": query,
                    "results": results,
                    "knowledge_base_id": self.config.knowledge_base_id,
                    "search_time": search_time,
                    "attempt": attempt + 1
                }
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                Logger.warn(f"Bedrock similarity_search client error (attempt {attempt + 1}/{self._max_retries}): {error_code} - {e}")
                
                if error_code in ['ResourceNotFoundException', 'AccessDeniedException']:
                    # 재시도해도 해결되지 않는 오류들
                    break
                    
            except EndpointConnectionError as e:
                self.metrics.connection_failures += 1
                Logger.warn(f"Bedrock connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                Logger.warn(f"Bedrock similarity_search error (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.metrics.failed_operations += 1
        total_time = time.time() - start_time
        Logger.error(f"Bedrock similarity_search failed after {self._max_retries} attempts (total: {total_time:.3f}s)")
        return {
            "success": False,
            "error": f"Search failed after {self._max_retries} attempts",
            "total_time": total_time,
            "attempts": self._max_retries
        }
    
    async def similarity_search_by_vector(self, vector: List[float], top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """벡터로 유사도 검색"""
        # Bedrock Knowledge Base는 벡터 직접 검색을 지원하지 않음
        # 대신 텍스트 기반 검색을 사용하거나 다른 벡터 DB와 연동 필요
        Logger.warn("Bedrock Knowledge Base does not support direct vector search")
        return {
            "success": False,
            "error": "Direct vector search not supported by Bedrock Knowledge Base"
        }
    
    async def add_documents(self, documents: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """문서 추가 (Knowledge Base는 S3를 통해 관리)"""
        Logger.warn("Document addition should be done through S3 and Knowledge Base sync")
        return {
            "success": False,
            "error": "Documents should be added through S3 and Knowledge Base synchronization"
        }
    
    async def delete_documents(self, document_ids: List[str], **kwargs) -> Dict[str, Any]:
        """문서 삭제 (Knowledge Base는 S3를 통해 관리)"""
        Logger.warn("Document deletion should be done through S3 and Knowledge Base sync")
        return {
            "success": False,
            "error": "Documents should be deleted through S3 and Knowledge Base synchronization"
        }
    
    async def update_document(self, document_id: str, document: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """문서 업데이트 (Knowledge Base는 S3를 통해 관리)"""
        Logger.warn("Document update should be done through S3 and Knowledge Base sync")
        return {
            "success": False,
            "error": "Documents should be updated through S3 and Knowledge Base synchronization"
        }
    
    async def get_document(self, document_id: str, **kwargs) -> Dict[str, Any]:
        """문서 조회"""
        # Knowledge Base에서 직접 문서 조회는 제한적
        Logger.warn("Direct document retrieval not fully supported by Bedrock Knowledge Base")
        return {
            "success": False,
            "error": "Direct document retrieval not supported"
        }
    
    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """텍스트 생성 (향상된 에러 처리 및 메트릭)"""
        start_time = time.time()
        self.metrics.total_operations += 1
        self.metrics.last_operation_time = start_time
        
        for attempt in range(self._max_retries):
            try:
                client = await self._get_bedrock_runtime_client()
                
                model_id = kwargs.get('model_id', self.config.text_model)
                max_tokens = kwargs.get('max_tokens', 1000)
                temperature = kwargs.get('temperature', 0.7)
                
                # Claude 모델용 요청 형식
                if 'claude' in model_id:
                    body = {
                        "anthropic_version": "bedrock-2023-05-31",
                        "max_tokens": max_tokens,
                        "temperature": temperature,
                        "messages": [
                            {
                                "role": "user",
                                "content": prompt
                            }
                        ]
                    }
                else:
                    # 다른 모델용 일반 형식
                    body = {
                        "inputText": prompt,
                        "textGenerationConfig": {
                            "maxTokenCount": max_tokens,
                            "temperature": temperature
                        }
                    }
                
                async with client as bedrock:
                    response = await bedrock.invoke_model(
                        modelId=model_id,
                        body=json.dumps(body),
                        contentType='application/json',
                        accept='application/json'
                    )
                
                response_body = json.loads(await response['body'].read())
                
                # Claude 모델 응답 파싱
                if 'claude' in model_id:
                    generated_text = response_body.get('content', [{}])[0].get('text', '')
                else:
                    generated_text = response_body.get('results', [{}])[0].get('outputText', '')
                
                # 성공 메트릭
                generation_time = time.time() - start_time
                self.metrics.successful_operations += 1
                self.metrics.total_generation_time += generation_time
                self.metrics.texts_generated += 1
                
                Logger.debug(f"Bedrock generate_text success: {len(generated_text)} characters ({generation_time:.3f}s)")
                return {
                    "success": True,
                    "prompt": prompt,
                    "generated_text": generated_text,
                    "model": model_id,
                    "generation_time": generation_time,
                    "attempt": attempt + 1
                }
                
            except ClientError as e:
                error_code = e.response.get('Error', {}).get('Code', 'Unknown')
                self.metrics.model_errors += 1
                Logger.warn(f"Bedrock generate_text client error (attempt {attempt + 1}/{self._max_retries}): {error_code} - {e}")
                
                if error_code in ['ValidationException', 'AccessDeniedException', 'ThrottlingException']:
                    # 재시도해도 해결되지 않는 오류들 (Throttling은 재시도 가능하지만 별도 처리)
                    if error_code != 'ThrottlingException':
                        break
                    
            except EndpointConnectionError as e:
                self.metrics.connection_failures += 1
                Logger.warn(f"Bedrock connection error (attempt {attempt + 1}/{self._max_retries}): {e}")
                
            except Exception as e:
                Logger.warn(f"Bedrock generate_text error (attempt {attempt + 1}/{self._max_retries}): {e}")
            
            # 재시도 대기
            if attempt < self._max_retries - 1:
                delay = self._retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        self.metrics.failed_operations += 1
        total_time = time.time() - start_time
        Logger.error(f"Bedrock generate_text failed after {self._max_retries} attempts (total: {total_time:.3f}s)")
        return {
            "success": False,
            "error": f"Text generation failed after {self._max_retries} attempts",
            "total_time": total_time,
            "attempts": self._max_retries
        }
    
    async def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """채팅 완성"""
        try:
            client = await self._get_bedrock_runtime_client()
            
            model_id = kwargs.get('model_id', self.config.text_model)
            max_tokens = kwargs.get('max_tokens', 1000)
            temperature = kwargs.get('temperature', 0.7)
            
            # Claude 모델용 요청 형식
            if 'claude' in model_id:
                body = {
                    "anthropic_version": "bedrock-2023-05-31",
                    "max_tokens": max_tokens,
                    "temperature": temperature,
                    "messages": messages
                }
            else:
                # 다른 모델의 경우 메시지를 단일 프롬프트로 변환
                prompt = "\n".join([f"{msg['role']}: {msg['content']}" for msg in messages])
                return await self.generate_text(prompt, **kwargs)
            
            async with client as bedrock:
                response = await bedrock.invoke_model(
                    modelId=model_id,
                    body=json.dumps(body),
                    contentType='application/json',
                    accept='application/json'
                )
            
            response_body = json.loads(await response['body'].read())
            generated_text = response_body.get('content', [{}])[0].get('text', '')
            
            Logger.debug(f"Bedrock chat_completion success: {len(generated_text)} characters")
            return {
                "success": True,
                "messages": messages,
                "response": generated_text,
                "model": model_id
            }
            
        except Exception as e:
            Logger.error(f"Bedrock chat_completion failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    # === 모니터링 및 관리 메소드들 ===
    
    async def health_check(self) -> Dict[str, Any]:
        """Bedrock 연결 상태 확인"""
        start_time = time.time()
        
        try:
            # Bedrock 기본 연결 확인
            bedrock_client = await self._get_bedrock_client()
            
            async with bedrock_client as client:
                # Foundation 모델 목록 조회로 연결 확인
                models_response = await client.list_foundation_models()
            
            # Runtime 클라이언트 확인
            runtime_client = await self._get_bedrock_runtime_client()
            
            response_time = time.time() - start_time
            self.connection_state = ConnectionState.HEALTHY
            self._last_health_check = time.time()
            
            return {
                "healthy": True,
                "response_time": response_time,
                "connection_state": self.connection_state.value,
                "region": self.config.aws_region,
                "available_models": len(models_response.get('modelSummaries', [])),
                "embedding_model": getattr(self.config, 'embedding_model', 'unknown'),
                "text_model": getattr(self.config, 'text_model', 'unknown'),
                "knowledge_base_id": getattr(self.config, 'knowledge_base_id', None),
                "metrics": self.get_metrics()
            }
            
        except NoCredentialsError as e:
            return {
                "healthy": False,
                "error": f"Credentials error: {e}",
                "error_type": "credentials",
                "connection_state": ConnectionState.FAILED.value,
                "metrics": self.get_metrics()
            }
        except EndpointConnectionError as e:
            self.connection_state = ConnectionState.FAILED
            return {
                "healthy": False,
                "error": f"Connection error: {e}",
                "error_type": "connection",
                "connection_state": self.connection_state.value,
                "metrics": self.get_metrics()
            }
        except Exception as e:
            self.connection_state = ConnectionState.DEGRADED
            return {
                "healthy": False,
                "error": str(e),
                "error_type": "unknown",
                "connection_state": self.connection_state.value,
                "metrics": self.get_metrics()
            }
    
    def get_metrics(self) -> Dict[str, Any]:
        """Bedrock VectorDB 클라이언트 메트릭 조회"""
        avg_embedding_time = 0.0
        avg_search_time = 0.0
        avg_generation_time = 0.0
        success_rate = 0.0
        
        if self.metrics.texts_embedded > 0:
            avg_embedding_time = self.metrics.total_embedding_time / self.metrics.texts_embedded
        
        if self.metrics.searches_performed > 0:
            avg_search_time = self.metrics.total_search_time / self.metrics.searches_performed
        
        if self.metrics.texts_generated > 0:
            avg_generation_time = self.metrics.total_generation_time / self.metrics.texts_generated
        
        if self.metrics.total_operations > 0:
            success_rate = self.metrics.successful_operations / self.metrics.total_operations
        
        return {
            "total_operations": self.metrics.total_operations,
            "successful_operations": self.metrics.successful_operations,
            "failed_operations": self.metrics.failed_operations,
            "success_rate": success_rate,
            "average_embedding_time": avg_embedding_time,
            "average_search_time": avg_search_time,
            "average_generation_time": avg_generation_time,
            "texts_embedded": self.metrics.texts_embedded,
            "searches_performed": self.metrics.searches_performed,
            "texts_generated": self.metrics.texts_generated,
            "connection_failures": self.metrics.connection_failures,
            "credential_errors": self.metrics.credential_errors,
            "timeout_errors": self.metrics.timeout_errors,
            "model_errors": self.metrics.model_errors,
            "last_operation_time": self.metrics.last_operation_time,
            "connection_state": self.connection_state.value,
            "last_health_check": self._last_health_check
        }
    
    def reset_metrics(self):
        """메트릭 초기화"""
        self.metrics = VectorDbMetrics()
        Logger.info("Bedrock VectorDB client metrics reset")
    
    async def close(self):
        """클라이언트 종료"""
        if self._bedrock_client:
            try:
                async with self._bedrock_client as client:
                    pass
            except:
                pass
            self._bedrock_client = None
        
        if self._bedrock_runtime_client:
            try:
                async with self._bedrock_runtime_client as client:
                    pass
            except:
                pass
            self._bedrock_runtime_client = None
        
        if self._knowledge_base_client:
            try:
                async with self._knowledge_base_client as client:
                    pass
            except:
                pass
            self._knowledge_base_client = None
        
        if self._session:
            try:
                await self._session.close()
            except:
                pass
            self._session = None
        
        Logger.info("Bedrock VectorDB client closed")
        
        # 최종 메트릭 로깅
        final_metrics = self.get_metrics()
        Logger.info(f"Final Bedrock VectorDB metrics: {final_metrics}")