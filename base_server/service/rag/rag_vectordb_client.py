"""
RAG 서비스 전용 벡터 데이터베이스 클라이언트
동기 boto3 + asyncio.run_in_executor 패턴으로 coroutine 재사용 문제 해결
다른 서비스에 영향을 주지 않고 RAG 서비스만을 위한 안전한 클라이언트
"""

import asyncio
import time
import random
import json
import re
from typing import List, Dict, Any, Optional
from concurrent.futures import ThreadPoolExecutor
import boto3
from botocore.exceptions import ClientError

from service.core.logger import Logger
from service.vectordb.vectordb_client import IVectorDbClient
from service.vectordb.bedrock_vectordb_client import ConnectionState, VectorDbMetrics
from dataclasses import dataclass

@dataclass
class RagVectorDbConfig:
    """RAG 전용 벡터 DB 설정"""
    aws_access_key_id: str
    aws_secret_access_key: str
    region_name: str
    knowledge_base_id: str
    aws_session_token: Optional[str] = None
    max_retries: int = 3
    retry_delay_base: float = 1.0
    timeout: float = 30.0

class RagVectorDbClient(IVectorDbClient):
    """
    RAG 서비스 전용 VectorDB 클라이언트 (AWS Bedrock Knowledge Base)
    다른 서비스에 영향을 주지 않으면서 클라이언트 재사용 및 비동기 호출 문제 해결
    """
    _knowledge_base_client = None
    _session = None
    _executor = None
    _is_initialized = False
    _config: Optional[RagVectorDbConfig] = None
    metrics = VectorDbMetrics()
    _last_health_check = 0

    def __init__(self, config: RagVectorDbConfig):
        if not RagVectorDbClient._is_initialized:
            RagVectorDbClient._config = config
            RagVectorDbClient._executor = ThreadPoolExecutor(max_workers=10) # 병렬 처리 워커 수
            RagVectorDbClient._is_initialized = True
            Logger.info("RagVectorDbClient 초기화 완료")
        else:
            Logger.info("RagVectorDbClient는 이미 초기화되었습니다.")

    def _create_session(self):
        """Boto3 세션 생성 또는 재사용"""
        if self._session is None:
            self._session = boto3.Session(
                aws_access_key_id=self._config.aws_access_key_id,
                aws_secret_access_key=self._config.aws_secret_access_key,
                region_name=self._config.region_name,
                aws_session_token=self._config.aws_session_token
            )
            Logger.debug("새로운 boto3 세션 생성")
        return self._session

    def _get_knowledge_base_client(self):
        """Bedrock Agent Runtime 클라이언트 생성 또는 재사용"""
        if self._knowledge_base_client is None:
            session = self._create_session()
            self._knowledge_base_client = session.client(
                'bedrock-agent-runtime',
                config=boto3.session.Config(
                    retries={'max_attempts': self._config.max_retries},
                    connect_timeout=self._config.timeout,
                    read_timeout=self._config.timeout
                )
            )
            Logger.debug("새로운 Bedrock Agent Runtime 클라이언트 생성")
        return self._knowledge_base_client

    def _extract_title_from_content(self, content: str) -> str:
        """컨텐츠에서 제목을 추출하는 정교한 로직"""
        if not content:
            return "No title"
        
        # 1. JSON 파싱 시도 (크롤러가 JSON 형태로 저장한 경우)
        try:
            # JSON 형태의 데이터에서 title 필드 추출
            if '"title":' in content or '"Title":' in content:
                title_match = re.search(r'"title":\s*"([^"]+)"', content, re.IGNORECASE)
                if title_match:
                    title = title_match.group(1).strip()
                    if 5 <= len(title) <= 200:
                        return title
        except:
            pass
        
        # 2. 크롤러 구조에 맞춘 제목 추출 패턴 (우선순위 순)
        title_patterns = [
            r'The news title is:\s*([^\n}]+)',  # JSON 구조 고려하여 } 전까지
            r'Title:\s*([^\n}]+)',  # JSON 구조 고려
            r'Headline:\s*([^\n}]+)',
            r'제목:\s*([^\n}]+)',
            r'"title":\s*"([^"]+)"',  # JSON 형태
            r'"Title":\s*"([^"]+)"',  # JSON 형태
        ]
        
        for pattern in title_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                potential_title = match.group(1).strip()
                # JSON 파싱 오류로 인한 불필요한 문자 제거
                potential_title = re.sub(r'"[^"]*$', '', potential_title)  # 끝의 불완전한 JSON 제거
                potential_title = re.sub(r'\{[^}]*$', '', potential_title)  # 끝의 불완전한 JSON 제거
                potential_title = potential_title.strip()
                
                # 제목으로 적합한 길이인지 확인 (5-200자)
                if 5 <= len(potential_title) <= 200:
                    return potential_title
        
        # 3. URL에서 파일명 추출 시도
        url_match = re.search(r'https?://[^\s]+', content)
        if url_match:
            url = url_match.group(0)
            # URL에서 의미있는 부분 추출
            if 'news/' in url:
                news_part = url.split('news/')[-1]
                if news_part and len(news_part) > 10:
                    return news_part[:100]  # URL 기반 제목 (최대 100자)
        
        return "No title"

    def _extract_source_from_content(self, content: str) -> str:
        """컨텐츠에서 출처를 추출하는 정교한 로직"""
        if not content:
            return "unknown"
        
        # 1. JSON 파싱 시도
        try:
            if '"source":' in content or '"Source":' in content:
                source_match = re.search(r'"source":\s*"([^"]+)"', content, re.IGNORECASE)
                if source_match:
                    source = source_match.group(1).strip()
                    if len(source) >= 3:
                        return source
        except:
            pass
        
        # 2. 크롤러 구조에 맞춘 출처 추출 패턴 (우선순위 순)
        source_patterns = [
            r'Source:\s*([^\n}]+)',  # JSON 구조 고려
            r'URL:\s*([^\n}]+)',
            r'link:\s*([^\n}]+)',
            r'publisher:\s*([^\n}]+)',
            r'"source":\s*"([^"]+)"',  # JSON 형태
            r'"Source":\s*"([^"]+)"',  # JSON 형태
        ]
        
        for pattern in source_patterns:
            match = re.search(pattern, content, re.IGNORECASE)
            if match:
                potential_source = match.group(1).strip()
                # JSON 파싱 오류로 인한 불필요한 문자 제거
                potential_source = re.sub(r'"[^"]*$', '', potential_source)
                potential_source = re.sub(r'\{[^}]*$', '', potential_source)
                potential_source = potential_source.strip()
                
                # 출처로 적합한 길이인지 확인 (3자 이상)
                if len(potential_source) >= 3:
                    return potential_source
        
        # 3. URL에서 도메인 추출
        url_match = re.search(r'https?://([^/\s]+)', content)
        if url_match:
            domain = url_match.group(1)
            if domain and len(domain) >= 3:
                return domain
        
        return "unknown"

    def _clean_content(self, content: str) -> str:
        """컨텐츠에서 메타데이터를 제거하고 순수한 내용만 추출"""
        if not content:
            return ""
        
        lines = content.split('\n')
        cleaned_lines = []
        
        # 제거할 메타데이터 패턴 목록 (소문자 변환 후 비교)
        metadata_patterns_to_remove = [
            'title:', 'ticker:', 'source:', 'date:', 'url:', 'content type:', 
            'task id:', 'collected at:', 'this is a financial news article',
            'the news title is:', 'published on:', 'headline:', '제목:'
        ]
        
        for line in lines:
            line_lower = line.lower().strip()
            
            # 메타데이터 패턴이 포함된 줄은 건너뛰기
            if any(pattern in line_lower for pattern in metadata_patterns_to_remove):
                continue
            
            # 빈 줄은 건너뛰기
            if not line.strip():
                continue
            
            cleaned_lines.append(line)
        
        # 정리된 컨텐츠 반환
        cleaned_content = '\n'.join(cleaned_lines).strip()
        
        # 만약 정리된 컨텐츠가 비어있으면 빈 문자열 반환
        return cleaned_content

    async def similarity_search(self, query: str, top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """
        주어진 쿼리에 대해 유사한 문서를 검색합니다.
        크롤러가 저장한 데이터 구조를 정확하게 파싱합니다.
        """
        if not self._is_initialized:
            Logger.error("RagVectorDbClient가 초기화되지 않았습니다.")
            return {'success': False, 'error': 'Client not initialized'}

        start_time = time.time()
        results = []
        
        for attempt in range(self._config.max_retries):
            try:
                client = self._get_knowledge_base_client()
                
                # 비동기 환경에서 동기 boto3 호출 실행
                response = await asyncio.get_running_loop().run_in_executor(
                    self._executor,
                    lambda: client.retrieve(
                        knowledgeBaseId=self._config.knowledge_base_id,
                        retrievalQuery={'text': query},
                        retrievalConfiguration={
                            'vectorSearchConfiguration': {
                                'numberOfResults': top_k
                            }
                        }
                    )
                )
                
                for item in response.get('retrievalResults', []):
                    # 원본 컨텐츠 추출
                    original_content = ""
                    if 'content' in item and 'text' in item['content']:
                        original_content = item['content']['text']
                    
                    # 메타데이터 추출 - 다양한 가능한 구조 시도
                    metadata = {}
                    if 'metadata' in item:
                        metadata = item['metadata']
                    elif 'content' in item and isinstance(item['content'], dict) and 'metadata' in item['content']:
                        metadata = item['content']['metadata']
                    
                    # 1. 메타데이터에서 제목과 출처 추출 (최우선)
                    title = metadata.get('title') or metadata.get('Title') or "No title"
                    source = (metadata.get('source') or 
                             metadata.get('Source') or 
                             metadata.get('url') or 
                             metadata.get('URL') or 
                             metadata.get('link') or
                             "unknown")
                    
                    # 2. 메타데이터에 없으면 컨텐츠에서 패턴 매칭으로 추출
                    if title == "No title":
                        title = self._extract_title_from_content(original_content)
                    
                    if source == "unknown":
                        source = self._extract_source_from_content(original_content)
                    
                    # 3. S3 위치에서 파일명 추출 시도 (마지막 수단)
                    if title == "No title" and 'location' in item:
                        s3_uri = item['location'].get('s3Location', {}).get('uri', '')
                        if s3_uri:
                            file_name = s3_uri.split('/')[-1] if '/' in s3_uri else s3_uri
                            if not file_name.endswith('.json'):
                                title = file_name if file_name else "No title"
                            if source == "unknown":
                                source = s3_uri
                    
                    # 4. 컨텐츠 정리 (메타데이터 제거)
                    cleaned_content = self._clean_content(original_content)
                    
                    # 5. 정리된 컨텐츠가 비어있고 제목이 있다면 제목을 컨텐츠로 사용 (최후의 수단)
                    if not cleaned_content and title != "No title":
                        cleaned_content = title
                    
                    result = {
                        'id': item.get('location', {}).get('s3Location', {}).get('uri', ''),
                        'content': cleaned_content,
                        'metadata': {
                            'title': title,
                            'source': source,
                            'original_metadata': metadata
                        },
                        'score': item.get('score', 0.0)
                    }
                    results.append(result)
                
                search_time = time.time() - start_time
                self.metrics.successful_operations += 1
                self.metrics.total_search_time += search_time
                self.metrics.searches_performed += 1
                
                Logger.debug(f"RAG VectorDB similarity_search 성공: {len(results)}개 결과 ({search_time:.3f}초)")
                
                return {
                    'success': True,
                    'results': results,
                    'total': len(results),
                    'search_time': search_time,
                    'query': query
                }
                
            except ClientError as ce:
                error_code = ce.response.get("Error", {}).get("Code")
                error_message = ce.response.get("Error", {}).get("Message")
                Logger.warn(f"RAG VectorDB similarity_search ClientError (시도 {attempt + 1}/{self._config.max_retries}): {error_code} - {error_message}")
                self.metrics.failed_operations += 1
                if error_code == "ValidationException" and "Knowledge base" in error_message and "not found" in error_message:
                    return {'success': False, 'error': f"Knowledge Base ID가 유효하지 않거나 찾을 수 없습니다: {error_message}"}
                if "ThrottlingException" in error_code:
                    Logger.warn("Bedrock API 호출 제한 발생, 재시도합니다.")
                
            except Exception as e:
                Logger.warn(f"RAG VectorDB similarity_search 오류 (시도 {attempt + 1}/{self._config.max_retries}): {e}")
                
                # 연결 오류 시 클라이언트 재생성
                if "closed" in str(e).lower() or "connection" in str(e).lower():
                    self._knowledge_base_client = None
                    self.metrics.connection_failures += 1
                
                self.metrics.failed_operations += 1
            
            # 재시도 전 대기
            if attempt < self._config.max_retries - 1:
                delay = self._config.retry_delay_base * (2 ** attempt) + random.uniform(0, 1)
                await asyncio.sleep(delay)
        
        # 모든 재시도 실패
        total_time = time.time() - start_time
        self.metrics.failed_operations += 1
        Logger.error(f"RAG VectorDB similarity_search {self._config.max_retries}회 시도 후 실패 (총 {total_time:.3f}초)")
        
        return {
            'success': False,
            'error': f'검색 실패 (총 {total_time:.3f}초)',
            'results': [],
            'total': 0,
            'search_time': total_time,
            'query': query
        }
    
    async def similarity_search_by_vector(self, vector: List[float], top_k: int = 10, **kwargs) -> Dict[str, Any]:
        """
        벡터 기반 유사도 검색 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: similarity_search_by_vector는 지원하지 않습니다")
        return {
            'success': False,
            'error': 'RAG VectorDB에서는 벡터 기반 검색을 지원하지 않습니다',
            'results': [],
            'total': 0
        }
    
    async def add_documents(self, documents: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        문서 추가 - RAG에서는 사용하지 않음 (RAG 서비스에서 처리)
        """
        Logger.warn("RAG VectorDB: add_documents는 RAG 서비스에서 처리됩니다")
        return {
            'success': False,
            'error': 'RAG VectorDB에서는 직접 문서 추가를 지원하지 않습니다',
            'total_documents': 0
        }
    
    async def delete_documents(self, document_ids: List[str], **kwargs) -> Dict[str, Any]:
        """
        문서 삭제 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: delete_documents는 지원하지 않습니다")
        return {
            'success': False,
            'error': 'RAG VectorDB에서는 문서 삭제를 지원하지 않습니다',
            'deleted_count': 0
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """
        상태 확인
        """
        try:
            # 간단한 연결 테스트
            client = self._get_knowledge_base_client()
            
            # Knowledge Base 상태 확인 호출
            # list_knowledge_bases는 권한이 필요하며, 간단한 연결 테스트용으로 적합하지 않을 수 있음.
            # 대신 retrieve API를 더미 쿼리로 호출하여 연결 확인
            await asyncio.get_running_loop().run_in_executor(
                self._executor,
                lambda: client.retrieve(
                    knowledgeBaseId=self._config.knowledge_base_id,
                    retrievalQuery={'text': 'health check query'},
                    retrievalConfiguration={
                        'vectorSearchConfiguration': {
                            'numberOfResults': 1
                        }
                    }
                )
            )
            self.metrics.successful_operations += 1
            return {'success': True, 'message': 'RagVectorDbClient is healthy'}
        except Exception as e:
            Logger.error(f"RagVectorDbClient health check 실패: {e}")
            self.metrics.failed_operations += 1
            return {'success': False, 'error': str(e)}
    
    def get_metrics(self) -> Dict[str, Any]:
        """
        클라이언트 메트릭 반환
        """
        # dataclass를 dict로 변환
        return {
            'total_operations': self.metrics.total_operations,
            'successful_operations': self.metrics.successful_operations,
            'failed_operations': self.metrics.failed_operations,
            'total_embedding_time': self.metrics.total_embedding_time,
            'total_search_time': self.metrics.total_search_time,
            'total_generation_time': self.metrics.total_generation_time,
            'texts_embedded': self.metrics.texts_embedded,
            'searches_performed': self.metrics.searches_performed,
            'texts_generated': self.metrics.texts_generated,
            'last_operation_time': self.metrics.last_operation_time,
            'connection_failures': self.metrics.connection_failures,
            'credential_errors': self.metrics.credential_errors,
            'timeout_errors': self.metrics.timeout_errors,
            'model_errors': self.metrics.model_errors
        }
    
    async def embed_text(self, text: str, **kwargs) -> Dict[str, Any]:
        """
        텍스트 임베딩 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: embed_text는 지원하지 않습니다")
        return {'success': False, 'error': 'RAG VectorDB에서는 텍스트 임베딩을 지원하지 않습니다'}

    async def embed_texts(self, texts: List[str], **kwargs) -> Dict[str, Any]:
        """
        여러 텍스트 임베딩 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: embed_texts는 지원하지 않습니다")
        return {'success': False, 'error': 'RAG VectorDB에서는 여러 텍스트 임베딩을 지원하지 않습니다'}

    async def update_document(self, document_id: str, document: Dict[str, Any], **kwargs) -> Dict[str, Any]:
        """
        문서 업데이트 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: update_document는 지원하지 않습니다")
        return {'success': False, 'error': 'RAG VectorDB에서는 문서 업데이트를 지원하지 않습니다'}

    async def get_document(self, document_id: str, **kwargs) -> Dict[str, Any]:
        """
        문서 조회 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: get_document는 지원하지 않습니다")
        return {'success': False, 'error': 'RAG VectorDB에서는 문서 조회를 지원하지 않습니다'}

    async def generate_text(self, prompt: str, **kwargs) -> Dict[str, Any]:
        """
        텍스트 생성 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: generate_text는 지원하지 않습니다")
        return {'success': False, 'error': 'RAG VectorDB에서는 텍스트 생성을 지원하지 않습니다'}

    async def chat_completion(self, messages: List[Dict[str, Any]], **kwargs) -> Dict[str, Any]:
        """
        챗봇 완성 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: chat_completion은 지원하지 않습니다")
        return {'success': False, 'error': 'RAG VectorDB에서는 챗봇 완성을 지원하지 않습니다'}

    async def start_ingestion_job(self, data_source_id: str, **kwargs) -> Dict[str, Any]:
        """
        수집 작업 시작 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: start_ingestion_job은 지원하지 않습니다")
        return {'success': False, 'error': 'RAG VectorDB에서는 수집 작업 시작을 지원하지 않습니다'}

    async def get_ingestion_job(self, data_source_id: str, ingestion_job_id: str, **kwargs) -> Dict[str, Any]:
        """
        수집 작업 상태 조회 - RAG에서는 사용하지 않음
        """
        Logger.warn("RAG VectorDB: get_ingestion_job은 지원하지 않습니다")
        return {'success': False, 'error': 'RAG VectorDB에서는 수집 작업 상태 조회를 지원하지 않습니다'}
    
    async def get_knowledge_base_status(self, **kwargs) -> Dict[str, Any]:
        """
        Knowledge Base 상태 조회
        """
        try:
            client = self._get_knowledge_base_client()
            response = await asyncio.get_running_loop().run_in_executor(
                self._executor,
                lambda: client.get_knowledge_base(knowledgeBaseId=self._config.knowledge_base_id)
            )
            status = response.get('knowledgeBase', {}).get('status', 'Unknown')
            return {'success': True, 'status': status}
        except Exception as e:
            Logger.error(f"Knowledge Base 상태 조회 실패: {e}")
            return {'success': False, 'error': str(e)}
    
    async def close(self):
        """
        클라이언트 및 스레드 풀 종료
        """
        if self._executor:
            self._executor.shutdown(wait=True)
            Logger.info("RagVectorDbClient 스레드 풀 종료")
        if self._knowledge_base_client:
            # boto3 클라이언트는 명시적 close 메서드가 없음. 참조 해제.
            self._knowledge_base_client = None
            Logger.info("RagVectorDbClient Bedrock 클라이언트 참조 해제")
        self._session = None
        self._is_initialized = False
        Logger.info("RagVectorDbClient 종료 완료") 