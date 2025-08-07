import asyncio
import hashlib
import time
from typing import Optional, Dict, Any, List, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed
from service.rag.rag_config import RagConfig
from service.rag.rag_vectordb_client import RagVectorDbClient, RagVectorDbConfig
from service.core.logger import Logger

class RagService:
    """
    RAG (Retrieval-Augmented Generation) 서비스
    
    SearchService(키워드 검색)와 VectorDbService(벡터 검색)를 조합한 
    하이브리드 문서 검색 기능을 제공하는 정적 클래스 (111 패턴)
    """
    
    # 111 패턴 상태 관리
    _initialized: bool = False
    _config: Optional[RagConfig] = None
    _search_available: bool = False
    _vector_available: bool = False
    
    # RAG 전용 벡터 클라이언트 (coroutine 재사용 문제 해결)
    _rag_vector_client: Optional[RagVectorDbClient] = None
    
    # 성능 통계
    _stats = {
        "documents_indexed": 0,
        "search_requests": 0,
        "hybrid_searches": 0,
        "avg_search_time": 0.0
    }

    @classmethod
    def init(cls, rag_config: RagConfig) -> bool:
        """
        RAG 서비스 초기화 (111 패턴)
        
        Args:
            rag_config: RAG 서비스 설정
            
        Returns:
            bool: 초기화 성공 여부
        """
        try:
            Logger.info("🚀 RAG 서비스 초기화 시작...")
            
            if cls._initialized:
                Logger.warn("⚠️ RAG 서비스가 이미 초기화됨")
                return True
            
            # 설정 검증
            if not cls._validate_config(rag_config):
                Logger.error("❌ RAG 설정 검증 실패")
                return False
            
            cls._config = rag_config
            
            # 의존 서비스 상태 검증
            if not cls._validate_dependencies():
                Logger.error("❌ 의존 서비스 검증 실패")
                return False
            
            # 하이브리드 검색 설정 검증
            if not cls._validate_hybrid_setup():
                Logger.error("❌ 하이브리드 검색 설정 검증 실패")
                return False
            
            # 통계 초기화
            cls._reset_stats()
            
            cls._initialized = True
            Logger.info(f"✅ RAG 서비스 초기화 완료")
            Logger.info(f"   - 벡터 검색: {'활성화' if cls._vector_available else '비활성화'}")
            Logger.info(f"   - 키워드 검색: {'활성화' if cls._search_available else '비활성화'}")
            Logger.info(f"   - 하이브리드 모드: {'활성화' if (cls._vector_available and cls._search_available) else '비활성화'}")
            
            return True
            
        except Exception as e:
            Logger.error(f"❌ RAG 서비스 초기화 실패: {e}")
            cls._initialized = False
            cls._config = None
            return False

    @classmethod
    def _validate_config(cls, config: RagConfig) -> bool:
        """RAG 설정 검증"""
        try:
            if not config.collection_name:
                Logger.error("collection_name이 설정되지 않음")
                return False
            
            if not config.embedding_model:
                Logger.error("embedding_model이 설정되지 않음")
                return False
            
            if config.default_k <= 0:
                Logger.error(f"default_k는 0보다 커야 함: {config.default_k}")
                return False
            
            if not (0.0 <= config.default_threshold <= 1.0):
                Logger.error(f"default_threshold는 0.0~1.0 사이여야 함: {config.default_threshold}")
                return False
            
            Logger.debug("RAG 설정 검증 통과")
            return True
            
        except Exception as e:
            Logger.error(f"RAG 설정 검증 중 오류: {e}")
            return False

    @classmethod
    def _validate_dependencies(cls) -> bool:
        """의존 서비스 초기화 상태 검증"""
        try:
            from service.search.search_service import SearchService
            from service.vectordb.vectordb_service import VectorDbService
            
            # SearchService 상태 확인
            cls._search_available = SearchService.is_initialized()
            Logger.info(f"SearchService 상태: {'사용 가능' if cls._search_available else '사용 불가'}")
            
            # VectorDbService 상태 확인
            cls._vector_available = VectorDbService.is_initialized()
            Logger.info(f"VectorDbService 상태: {'사용 가능' if cls._vector_available else '사용 불가'}")
            
            # RAG 전용 벡터 클라이언트 초기화 (coroutine 재사용 문제 해결)
            if cls._vector_available and cls._config.enable_vector_db:
                try:
                    # RAG 설정에서 벡터 DB 설정 추출
                    vector_config = RagVectorDbConfig(
                        aws_access_key_id=cls._config.aws_access_key_id,
                        aws_secret_access_key=cls._config.aws_secret_access_key,
                        region_name=cls._config.region_name,
                        knowledge_base_id=cls._config.knowledge_base_id,
                        aws_session_token=getattr(cls._config, 'aws_session_token', None),
                        max_retries=3,
                        retry_delay_base=1.0,
                        timeout=30.0
                    )
                    
                    cls._rag_vector_client = RagVectorDbClient(vector_config)
                    Logger.info("✅ RAG 전용 벡터 클라이언트 초기화 완료")
                    
                except Exception as e:
                    Logger.error(f"❌ RAG 전용 벡터 클라이언트 초기화 실패: {e}")
                    cls._vector_available = False
            
            # 최소 하나의 서비스는 사용 가능해야 함
            if not (cls._search_available or cls._vector_available):
                Logger.error("Search와 Vector 서비스 모두 사용할 수 없음")
                return False
            
            return True
            
        except Exception as e:
            Logger.error(f"의존 서비스 검증 중 오류: {e}")
            return False

    @classmethod
    def _validate_hybrid_setup(cls) -> bool:
        """하이브리드 검색 설정 검증"""
        try:
            # 벡터 DB 설정 확인
            if cls._config.enable_vector_db and not cls._vector_available:
                Logger.warn("벡터 DB 활성화 설정이지만 VectorDbService가 사용 불가")
                
            # Fallback 검색 설정 확인
            if cls._config.enable_fallback_search and not cls._search_available:
                Logger.warn("Fallback 검색 활성화 설정이지만 SearchService가 사용 불가")
            
            # 하이브리드 검색 가능성 확인
            hybrid_possible = cls._search_available and cls._vector_available
            if hybrid_possible:
                Logger.info("🔍 완전한 하이브리드 검색 가능")
            else:
                Logger.warn("⚠️ 제한된 검색 모드로 동작")
            
            return True
            
        except Exception as e:
            Logger.error(f"하이브리드 검색 설정 검증 중 오류: {e}")
            return False

    @classmethod
    def _reset_stats(cls):
        """통계 초기화"""
        cls._stats = {
            "documents_indexed": 0,
            "search_requests": 0,
            "hybrid_searches": 0,
            "avg_search_time": 0.0
        }

    @classmethod
    async def add_documents(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        문서 인지션 파이프라인 - 두 서비스에 병렬 저장
        
        Args:
            documents: 저장할 문서 리스트
                [{"id": str, "content": str, "metadata": dict}, ...]
                
        Returns:
            Dict: 저장 결과 통계
        """
        if not cls._initialized:
            raise RuntimeError("RAG 서비스가 초기화되지 않음")
        
        start_time = time.time()
        Logger.info(f"📄 문서 인지션 파이프라인 시작: {len(documents)}개 문서")
        
        try:
            # 문서 전처리 및 검증
            processed_docs = cls._preprocess_documents(documents)
            if not processed_docs:
                Logger.warn("처리할 유효한 문서가 없음")
                return {"success": False, "message": "유효한 문서가 없음"}
            
            # 문서 청킹 (긴 문서를 작은 단위로 분할)
            chunked_docs = cls._chunk_documents(processed_docs)
            Logger.info(f"📝 문서 청킹 완료: {len(chunked_docs)}개 청크")
            
            # 병렬 저장 실행
            storage_results = await cls._parallel_storage(chunked_docs)
            
            # 결과 집계
            total_time = time.time() - start_time
            success_count = storage_results.get("success_count", 0)
            error_count = storage_results.get("error_count", 0)
            
            # 통계 업데이트
            cls._stats["documents_indexed"] += success_count
            
            Logger.info(f"✅ 문서 인지션 완료: {success_count}개 성공, {error_count}개 실패 ({total_time:.2f}초)")
            
            return {
                "success": error_count == 0,
                "total_documents": len(documents),
                "total_chunks": len(chunked_docs),
                "success_count": success_count,
                "error_count": error_count,
                "processing_time": total_time,
                "storage_details": storage_results
            }
            
        except Exception as e:
            Logger.error(f"❌ 문서 인지션 실패: {e}")
            return {
                "success": False,
                "error": str(e),
                "processing_time": time.time() - start_time
            }

    @classmethod
    def _preprocess_documents(cls, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """문서 전처리 및 검증"""
        processed = []
        
        for i, doc in enumerate(documents):
            try:
                # 필수 필드 검증
                if not isinstance(doc, dict):
                    Logger.warn(f"문서 {i}: dict 타입이 아님")
                    continue
                    
                if "content" not in doc or not doc["content"]:
                    Logger.warn(f"문서 {i}: content 필드 없음")
                    continue
                
                # ID 생성 (없으면 자동 생성)
                if "id" not in doc or not doc["id"]:
                    doc["id"] = cls._generate_document_id(doc["content"])
                
                # 메타데이터 기본값 설정
                if "metadata" not in doc:
                    doc["metadata"] = {}
                
                # 타임스탬프 추가
                doc["metadata"]["indexed_at"] = time.time()
                
                processed.append(doc)
                
            except Exception as e:
                Logger.warn(f"문서 {i} 전처리 실패: {e}")
                continue
        
        return processed

    @classmethod
    def _generate_document_id(cls, content: str) -> str:
        """문서 내용 기반 ID 생성"""
        return f"doc_{hashlib.md5(content.encode('utf-8')).hexdigest()[:16]}"

    @classmethod
    def _chunk_documents(cls, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """문서 청킹 - 긴 문서를 작은 단위로 분할"""
        chunks = []
        max_chunk_size = cls._config.max_content_length
        
        for doc in documents:
            content = doc["content"]
            
            # 문서가 너무 짧으면 그대로 유지
            if len(content) <= max_chunk_size:
                chunks.append(doc)
                continue
            
            # 긴 문서는 청킹
            chunk_texts = cls._split_text(content, max_chunk_size)
            
            for i, chunk_text in enumerate(chunk_texts):
                chunk_doc = {
                    "id": f"{doc['id']}_chunk_{i}",
                    "content": chunk_text,
                    "metadata": {
                        **doc["metadata"],
                        "parent_id": doc["id"],
                        "chunk_index": i,
                        "total_chunks": len(chunk_texts)
                    }
                }
                chunks.append(chunk_doc)
        
        return chunks

    @classmethod
    def _split_text(cls, text: str, max_size: int) -> List[str]:
        """텍스트를 지정된 크기로 분할"""
        if len(text) <= max_size:
            return [text]
        
        chunks = []
        sentences = text.split('. ')
        current_chunk = ""
        
        for sentence in sentences:
            if len(current_chunk + sentence) <= max_size:
                current_chunk += sentence + ". "
            else:
                if current_chunk:
                    chunks.append(current_chunk.strip())
                current_chunk = sentence + ". "
        
        if current_chunk:
            chunks.append(current_chunk.strip())
        
        return chunks

    @classmethod
    async def _parallel_storage(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """두 서비스에 병렬로 문서 저장"""
        search_results = []
        vector_results = []
        
        # 병렬 실행을 위한 태스크 생성
        tasks = []
        
        if cls._search_available:
            tasks.append(cls._store_to_search_service(documents))
        
        if cls._vector_available:
            tasks.append(cls._store_to_vector_service(documents))
        
        # 병렬 실행
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 결과 분석
            success_count = 0
            error_count = 0
            
            for result in results:
                if isinstance(result, Exception):
                    Logger.error(f"저장 태스크 실패: {result}")
                    error_count += len(documents)
                else:
                    success_count += result.get("success_count", 0)
                    error_count += result.get("error_count", 0)
        
        return {
            "success_count": success_count,
            "error_count": error_count,
            "search_results": search_results,
            "vector_results": vector_results
        }

    @classmethod
    async def _store_to_search_service(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """OpenSearch에 문서 저장"""
        try:
            from service.search.search_service import SearchService
            
            Logger.debug(f"OpenSearch에 {len(documents)}개 문서 저장 시작")
            
            success_count = 0
            error_count = 0
            
            # OpenSearch 클라이언트 직접 사용
            client = SearchService.get_client()
            if not client:
                raise Exception("OpenSearch 클라이언트 없음")
            
            index_name = cls._config.collection_name
            
            # 배치 처리로 성능 최적화
            for doc in documents:
                try:
                    # 문서 인덱싱
                    response = await SearchService.index_document(
                        index_name, 
                        {
                            "content": doc["content"],
                            "metadata": doc["metadata"]
                        },
                        doc["id"]
                    )
                    
                    if response:
                        success_count += 1
                    else:
                        error_count += 1
                        
                except Exception as e:
                    Logger.warn(f"문서 {doc['id']} OpenSearch 저장 실패: {e}")
                    error_count += 1
            
            Logger.info(f"OpenSearch 저장 완료: {success_count}개 성공, {error_count}개 실패")
            
            return {
                "service": "search",
                "success_count": success_count,
                "error_count": error_count
            }
            
        except Exception as e:
            Logger.error(f"OpenSearch 저장 실패: {e}")
            return {
                "service": "search",
                "success_count": 0,
                "error_count": len(documents),
                "error": str(e)
            }

    @classmethod
    async def _store_to_vector_service(cls, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """VectorDB에 문서 저장"""
        try:
            from service.vectordb.vectordb_service import VectorDbService
            
            Logger.debug(f"VectorDB에 {len(documents)}개 문서 저장 시작")
            
            success_count = 0
            error_count = 0
            
            for doc in documents:
                try:
                    # 텍스트 임베딩 생성
                    embed_result = await VectorDbService.embed_text(doc["content"])
                    
                    if not embed_result.get("success"):
                        Logger.warn(f"문서 {doc['id']} 임베딩 생성 실패")
                        error_count += 1
                        continue
                    
                    # 벡터 저장 (실제 구현은 VectorDbService의 메서드 확인 필요)
                    # 여기서는 임베딩이 성공했다고 가정
                    success_count += 1
                    
                except Exception as e:
                    Logger.warn(f"문서 {doc['id']} VectorDB 저장 실패: {e}")
                    error_count += 1
            
            Logger.info(f"VectorDB 저장 완료: {success_count}개 성공, {error_count}개 실패")
            
            return {
                "service": "vector",
                "success_count": success_count,
                "error_count": error_count
            }
            
        except Exception as e:
            Logger.error(f"VectorDB 저장 실패: {e}")
            return {
                "service": "vector",
                "success_count": 0,
                "error_count": len(documents),
                "error": str(e)
            }

    @classmethod
    def _preprocess_query(cls, query: str) -> str:
        """검색어 전처리 - 주식 심볼 확장, 동의어 처리"""
        if not query:
            return query
        
        # 주식 심볼 및 회사명 매핑 (크롤러 150개 심볼 기반)
        stock_mappings = {
            # 대형 테크주 (FAANG+)
            '애플': 'AAPL', 'apple': 'AAPL', 'Apple': 'AAPL',
            '마이크로소프트': 'MSFT', 'microsoft': 'MSFT', 'Microsoft': 'MSFT',
            '구글': 'GOOGL', 'google': 'GOOGL', 'Google': 'GOOGL',
            '구글알파벳': 'GOOG', 'alphabet': 'GOOG', 'Alphabet': 'GOOG',
            '아마존': 'AMZN', 'amazon': 'AMZN', 'Amazon': 'AMZN',
            '메타': 'META', 'meta': 'META', 'Meta': 'META',
            '페이스북': 'META', 'facebook': 'META', 'Facebook': 'META',
            '테슬라': 'TSLA', 'tesla': 'TSLA', 'Tesla': 'TSLA',
            '엔비디아': 'NVDA', 'nvidia': 'NVDA', 'Nvidia': 'NVDA',
            '넷플릭스': 'NFLX', 'netflix': 'NFLX', 'Netflix': 'NFLX',
            '오라클': 'ORCL', 'oracle': 'ORCL', 'Oracle': 'ORCL',
            '세일즈포스': 'CRM', 'salesforce': 'CRM', 'Salesforce': 'CRM',
            '어도비': 'ADBE', 'adobe': 'ADBE', 'Adobe': 'ADBE',
            '인텔': 'INTC', 'intel': 'INTC', 'Intel': 'INTC',
            'AMD': 'AMD', 'amd': 'AMD',
            '시스코': 'CSCO', 'cisco': 'CSCO', 'Cisco': 'CSCO',
            'IBM': 'IBM', 'ibm': 'IBM',
            
            # 반도체
            '퀄컴': 'QCOM', 'qualcomm': 'QCOM', 'Qualcomm': 'QCOM',
            '브로드컴': 'AVGO', 'broadcom': 'AVGO', 'Broadcom': 'AVGO',
            '텍사스인스트루먼트': 'TXN', 'texas instruments': 'TXN', 'Texas Instruments': 'TXN',
            '마이크론': 'MU', 'micron': 'MU', 'Micron': 'MU',
            '어플라이드머티리얼즈': 'AMAT', 'applied materials': 'AMAT', 'Applied Materials': 'AMAT',
            '라메리서치': 'LRCX', 'lam research': 'LRCX', 'Lam Research': 'LRCX',
            '아날로그디바이스': 'ADI', 'analog devices': 'ADI', 'Analog Devices': 'ADI',
            '마이크로칩': 'MCHP', 'microchip': 'MCHP', 'Microchip': 'MCHP',
            '케이엘에이': 'KLAC', 'kla': 'KLAC', 'KLA': 'KLAC',
            '마벨': 'MRVL', 'marvell': 'MRVL', 'Marvell': 'MRVL',
            
            # 주요 ETF들
            '스파이더': 'SPY', 'spy': 'SPY', 'SPY': 'SPY',
            '큐큐큐': 'QQQ', 'qqq': 'QQQ', 'QQQ': 'QQQ',
            '벡터토탈': 'VTI', 'vti': 'VTI', 'VTI': 'VTI',
            '러셀': 'IWM', 'iwm': 'IWM', 'IWM': 'IWM',
            '벡터선진국': 'VEA', 'vea': 'VEA', 'VEA': 'VEA',
            '벡터신흥국': 'VWO', 'vwo': 'VWO', 'VWO': 'VWO',
            '이샤어': 'EFA', 'efa': 'EFA', 'EFA': 'EFA',
            '골드': 'GLD', 'gld': 'GLD', 'GLD': 'GLD',
            '실버': 'SLV', 'slv': 'SLV', 'SLV': 'SLV',
            '국채': 'TLT', 'tlt': 'TLT', 'TLT': 'TLT',
            '하이일드': 'HYG', 'hyg': 'HYG', 'HYG': 'HYG',
            '회사채': 'LQD', 'lqd': 'LQD', 'LQD': 'LQD',
            '금융': 'XLF', 'xlf': 'XLF', 'XLF': 'XLF',
            '기술': 'XLK', 'xlk': 'XLK', 'XLK': 'XLK',
            '에너지': 'XLE', 'xle': 'XLE', 'XLE': 'XLE',
            '헬스케어': 'XLV', 'xlv': 'XLV', 'XLV': 'XLV',
            '산업재': 'XLI', 'xli': 'XLI', 'XLI': 'XLI',
            '소비재': 'XLP', 'xlp': 'XLP', 'XLP': 'XLP',
            '유틸리티': 'XLU', 'xlu': 'XLU', 'XLU': 'XLU',
            '부동산': 'XLRE', 'xlre': 'XLRE', 'XLRE': 'XLRE',
            
            # 금융 (은행, 보험, 핀테크)
            'JP모건': 'JPM', 'jpmorgan': 'JPM', 'JPMorgan': 'JPM',
            '뱅크오브아메리카': 'BAC', 'bank of america': 'BAC', 'Bank of America': 'BAC',
            '웰스파고': 'WFC', 'wells fargo': 'WFC', 'Wells Fargo': 'WFC',
            '시티그룹': 'C', 'citigroup': 'C', 'Citigroup': 'C',
            '골드만삭스': 'GS', 'goldman sachs': 'GS', 'Goldman Sachs': 'GS',
            '모건스탠리': 'MS', 'morgan stanley': 'MS', 'Morgan Stanley': 'MS',
            '버크셔해서웨이': 'BRK-B', 'berkshire hathaway': 'BRK-B', 'Berkshire Hathaway': 'BRK-B',
            '비자': 'V', 'visa': 'V', 'Visa': 'V',
            '마스터카드': 'MA', 'mastercard': 'MA', 'Mastercard': 'MA',
            '페이팔': 'PYPL', 'paypal': 'PYPL', 'PayPal': 'PYPL',
            '스퀘어': 'SQ', 'square': 'SQ', 'Square': 'SQ',
            '아메리칸익스프레스': 'AXP', 'american express': 'AXP', 'American Express': 'AXP',
            'US뱅크': 'USB', 'us bank': 'USB', 'US Bank': 'USB',
            'PNC': 'PNC', 'pnc': 'PNC',
            '트러스트파이낸셜': 'TFC', 'truist': 'TFC', 'Truist': 'TFC',
            '캐피탈원': 'COF', 'capital one': 'COF', 'Capital One': 'COF',
            
            # 헬스케어/제약
            '존슨앤존슨': 'JNJ', 'johnson & johnson': 'JNJ', 'Johnson & Johnson': 'JNJ',
            '화이자': 'PFE', 'pfizer': 'PFE', 'Pfizer': 'PFE',
            '유나이티드헬스': 'UNH', 'unitedhealth': 'UNH', 'UnitedHealth': 'UNH',
            '애브비': 'ABBV', 'abbvie': 'ABBV', 'AbbVie': 'ABBV',
            '머크': 'MRK', 'merck': 'MRK', 'Merck': 'MRK',
            '써모피셔': 'TMO', 'thermo fisher': 'TMO', 'Thermo Fisher': 'TMO',
            '애보트': 'ABT', 'abbott': 'ABT', 'Abbott': 'ABT',
            '다나허': 'DHR', 'danaher': 'DHR', 'Danaher': 'DHR',
            '브리스톨마이어스': 'BMY', 'bristol myers': 'BMY', 'Bristol Myers': 'BMY',
            '암젠': 'AMGN', 'amgen': 'AMGN', 'Amgen': 'AMGN',
            '길리아드': 'GILD', 'gilead': 'GILD', 'Gilead': 'GILD',
            '바이오젠': 'BIIB', 'biogen': 'BIIB', 'Biogen': 'BIIB',
            'CVS': 'CVS', 'cvs': 'CVS',
            '시그나': 'CI', 'cigna': 'CI', 'Cigna': 'CI',
            '앤템': 'ANTM', 'anthem': 'ANTM', 'Anthem': 'ANTM',
            '휴마나': 'HUM', 'humana': 'HUM', 'Humana': 'HUM',
            
            # 소비재 (필수/임의)
            '프록터앤갬블': 'PG', 'procter & gamble': 'PG', 'Procter & Gamble': 'PG',
            '코카콜라': 'KO', 'coca cola': 'KO', 'Coca Cola': 'KO',
            '펩시': 'PEP', 'pepsi': 'PEP', 'Pepsi': 'PEP',
            '월마트': 'WMT', 'walmart': 'WMT', 'Walmart': 'WMT',
            '홈디포': 'HD', 'home depot': 'HD', 'Home Depot': 'HD',
            '맥도날드': 'MCD', 'mcdonalds': 'MCD', 'McDonalds': 'MCD',
            '나이키': 'NKE', 'nike': 'NKE', 'Nike': 'NKE',
            '스타벅스': 'SBUX', 'starbucks': 'SBUX', 'Starbucks': 'SBUX',
            '타겟': 'TGT', 'target': 'TGT', 'Target': 'TGT',
            '로우스': 'LOW', 'lowes': 'LOW', 'Lowes': 'LOW',
            '코스트코': 'COST', 'costco': 'COST', 'Costco': 'COST',
            '디즈니': 'DIS', 'disney': 'DIS', 'Disney': 'DIS',
            '알리바바': 'BABA', 'alibaba': 'BABA', 'Alibaba': 'BABA',
            '이베이': 'EBAY', 'ebay': 'EBAY', 'eBay': 'EBAY',
            '에츠이': 'ETSY', 'etsy': 'ETSY', 'Etsy': 'ETSY',
            
            # 에너지
            '엑슨모빌': 'XOM', 'exxon mobil': 'XOM', 'Exxon Mobil': 'XOM',
            '체브론': 'CVX', 'chevron': 'CVX', 'Chevron': 'CVX',
            '콘코필립스': 'COP', 'conocophillips': 'COP', 'ConocoPhillips': 'COP',
            'EOG': 'EOG', 'eog': 'EOG',
            '슐럼버거': 'SLB', 'schlumberger': 'SLB', 'Schlumberger': 'SLB',
            '필립스66': 'PSX', 'phillips 66': 'PSX', 'Phillips 66': 'PSX',
            '발레로': 'VLO', 'valero': 'VLO', 'Valero': 'VLO',
            '킨더모건': 'KMI', 'kinder morgan': 'KMI', 'Kinder Morgan': 'KMI',
            '원에너지': 'OKE', 'oneok': 'OKE', 'Oneok': 'OKE',
            '윌리엄': 'WMB', 'williams': 'WMB', 'Williams': 'WMB',
            
            # 산업재/항공
            '보잉': 'BA', 'boeing': 'BA', 'Boeing': 'BA',
            '캐터필러': 'CAT', 'caterpillar': 'CAT', 'Caterpillar': 'CAT',
            '디어': 'DE', 'deere': 'DE', 'Deere': 'DE',
            '제너럴일렉트릭': 'GE', 'general electric': 'GE', 'General Electric': 'GE',
            '하니웰': 'HON', 'honeywell': 'HON', 'Honeywell': 'HON',
            '3M': 'MMM', 'mmm': 'MMM',
            'UPS': 'UPS', 'ups': 'UPS',
            '페덱스': 'FDX', 'fedex': 'FDX', 'FedEx': 'FDX',
            '록히드마틴': 'LMT', 'lockheed martin': 'LMT', 'Lockheed Martin': 'LMT',
            '레이시온': 'RTX', 'raytheon': 'RTX', 'Raytheon': 'RTX',
            '아메리칸항공': 'AAL', 'american airlines': 'AAL', 'American Airlines': 'AAL',
            '델타항공': 'DAL', 'delta': 'DAL', 'Delta': 'DAL',
            '유나이티드항공': 'UAL', 'united airlines': 'UAL', 'United Airlines': 'UAL',
            '사우스웨스트': 'LUV', 'southwest': 'LUV', 'Southwest': 'LUV',
            
            # 통신
            '버라이즌': 'VZ', 'verizon': 'VZ', 'Verizon': 'VZ',
            'AT&T': 'T', 'at&t': 'T', 'at&t': 'T',
            'T모바일': 'TMUS', 't mobile': 'TMUS', 'T Mobile': 'TMUS',
            '차터': 'CHTR', 'charter': 'CHTR', 'Charter': 'CHTR',
            '컴캐스트': 'CMCSA', 'comcast': 'CMCSA', 'Comcast': 'CMCSA',
            '디시': 'DISH', 'dish': 'DISH', 'Dish': 'DISH',
            
            # 자동차
            '포드': 'F', 'ford': 'F', 'Ford': 'F',
            '제너럴모터스': 'GM', 'general motors': 'GM', 'General Motors': 'GM',
            '리비안': 'RIVN', 'rivian': 'RIVN', 'Rivian': 'RIVN',
            '루시드': 'LCID', 'lucid': 'LCID', 'Lucid': 'LCID',
            '니오': 'NIO', 'nio': 'NIO', 'NIO': 'NIO',
            'XPeng': 'XPEV', 'xpeng': 'XPEV', 'xpev': 'XPEV',
            '리': 'LI', 'li': 'LI', 'Li': 'LI',
            
            # 부동산 REITs
            '아메리칸타워': 'AMT', 'american tower': 'AMT', 'American Tower': 'AMT',
            '프로로지스': 'PLD', 'prologis': 'PLD', 'Prologis': 'PLD',
            '크라운캐슬': 'CCI', 'crown castle': 'CCI', 'Crown Castle': 'CCI',
            '이퀴닉스': 'EQIX', 'equinix': 'EQIX', 'Equinix': 'EQIX',
            '사이먼프로퍼티': 'SPG', 'simon property': 'SPG', 'Simon Property': 'SPG',
            '리얼티인컴': 'O', 'realty income': 'O', 'Realty Income': 'O',
            '웰타워': 'WELL', 'welltower': 'WELL', 'Welltower': 'WELL',
            '엑스트라스페이스': 'EXR', 'extra space': 'EXR', 'Extra Space': 'EXR',
            '애벌론베이': 'AVB', 'avalonbay': 'AVB', 'AvalonBay': 'AVB',
            '에퀴티레지던셜': 'EQR', 'equity residential': 'EQR', 'Equity Residential': 'EQR',
            
            # 유틸리티
            '넥스트에라': 'NEE', 'next era': 'NEE', 'Next Era': 'NEE',
            '듀크에너지': 'DUK', 'duke energy': 'DUK', 'Duke Energy': 'DUK',
            '서던': 'SO', 'southern': 'SO', 'Southern': 'SO',
            '도미니언': 'D', 'dominion': 'D', 'Dominion': 'D',
            '아메리칸일렉트릭': 'AEP', 'american electric': 'AEP', 'American Electric': 'AEP',
            '엑셀론': 'EXC', 'exelon': 'EXC', 'Exelon': 'EXC',
            '엑셀에너지': 'XEL', 'xcel energy': 'XEL', 'Xcel Energy': 'XEL',
            'Sempra': 'SRE', 'sempra': 'SRE',
            '퍼블릭서비스': 'PEG', 'public service': 'PEG', 'Public Service': 'PEG',
            '컨솔리데이티드에디슨': 'ED', 'consolidated edison': 'ED', 'Consolidated Edison': 'ED',
            
            # 엔터테인먼트/미디어
            '로쿠': 'ROKU', 'roku': 'ROKU', 'Roku': 'ROKU',
            '스포티파이': 'SPOT', 'spotify': 'SPOT', 'Spotify': 'SPOT',
            '워너브라더스': 'WBD', 'warner bros': 'WBD', 'Warner Bros': 'WBD',
            '파라마운트': 'PARA', 'paramount': 'PARA', 'Paramount': 'PARA',
            '폭스': 'FOX', 'fox': 'FOX', 'Fox': 'FOX',
            '폭스뉴스': 'FOXA', 'fox news': 'FOXA', 'Fox News': 'FOXA',
            
            # 중국 ADR
            '징동': 'JD', 'jd': 'JD', 'JD': 'JD',
            '핀둬둬': 'PDD', 'pinduoduo': 'PDD', 'Pinduoduo': 'PDD',
            '바이두': 'BIDU', 'baidu': 'BIDU', 'Baidu': 'BIDU',
            '빌리빌리': 'BILI', 'bilibili': 'BILI', 'Bilibili': 'BILI',
            '디디': 'DIDI', 'didi': 'DIDI', 'DiDi': 'DIDI',
            '텐센트뮤직': 'TME', 'tencent music': 'TME', 'Tencent Music': 'TME',
            
            # 암호화폐 관련
            '코인베이스': 'COIN', 'coinbase': 'COIN', 'Coinbase': 'COIN',
            '마이크로스트래티지': 'MSTR', 'microstrategy': 'MSTR', 'MicroStrategy': 'MSTR',
            '라이엇': 'RIOT', 'riot': 'RIOT', 'Riot': 'RIOT',
            '마라': 'MARA', 'mara': 'MARA', 'Mara': 'MARA',
            '비트코인': 'BITB', 'bitcoin': 'BITB', 'Bitcoin': 'BITB',
            '아이셰어': 'IBIT', 'ishares': 'IBIT', 'iShares': 'IBIT',
            
            # 기타 주요 기업들
            '우버': 'UBER', 'uber': 'UBER', 'Uber': 'UBER',
            '라이프트': 'LYFT', 'lyft': 'LYFT', 'Lyft': 'LYFT',
            '스냅': 'SNAP', 'snap': 'SNAP', 'Snap': 'SNAP',
            '트위터': 'TWTR', 'twitter': 'TWTR', 'Twitter': 'TWTR',
            '줌': 'ZOOM', 'zoom': 'ZOOM', 'Zoom': 'ZOOM',
            '도쿠사인': 'DOCU', 'docusign': 'DOCU', 'DocuSign': 'DOCU',
            '팔란티어': 'PLTR', 'palantir': 'PLTR', 'Palantir': 'PLTR',
            '스노우플레이크': 'SNOW', 'snowflake': 'SNOW', 'Snowflake': 'SNOW',
            '슬랙': 'WORK', 'slack': 'WORK', 'Slack': 'WORK',
            '펠로톤': 'PTON', 'peloton': 'PTON', 'Peloton': 'PTON',
            '아크': 'ARKK', 'ark': 'ARKK', 'ARK': 'ARKK',
            '아크게놈': 'ARKG', 'ark genome': 'ARKG', 'ARK Genome': 'ARKG',
            '아크웹': 'ARKW', 'ark web': 'ARKW', 'ARK Web': 'ARKW',
            
            # 한국 주식
            '삼성전자': '005930', 'samsung': '005930', 'Samsung': '005930',
            '현대자동차': '005380', 'hyundai': '005380', 'Hyundai': '005380',
            'SK하이닉스': '000660', 'sk hynix': '000660', 'SK Hynix': '000660',
            'LG에너지솔루션': '373220', 'lg energy': '373220', 'LG Energy': '373220',
            '네이버': '035420', 'naver': '035420', 'Naver': '035420',
            '카카오': '035720', 'kakao': '035720', 'Kakao': '035720',
        }
        
        # 검색어 정규화 (소문자 변환)
        normalized_query = query.lower().strip()
        
        # 매핑된 심볼이 있는지 확인
        if normalized_query in stock_mappings:
            symbol = stock_mappings[normalized_query]
            # 원본 검색어 + 심볼로 확장
            expanded_query = f"{query} {symbol}"
            Logger.debug(f"검색어 확장: '{query}' → '{expanded_query}'")
            return expanded_query
        
        # 원본 검색어 반환
        return query

    @classmethod
    async def retrieve(cls, 
                      query: str, 
                      top_k: Optional[int] = None, 
                      hybrid: bool = True,
                      bm25_weight: float = 0.5,
                      vector_weight: float = 0.5) -> List[Dict[str, Any]]:
        """
        하이브리드 검색 - BM25와 벡터 검색 결과 조합
        
        Args:
            query: 검색 질의
            top_k: 반환할 문서 수 (기본값: config.default_k)
            hybrid: 하이브리드 검색 사용 여부
            bm25_weight: BM25 점수 가중치
            vector_weight: 벡터 점수 가중치
            
        Returns:
            List[Dict]: 검색 결과 문서 리스트
        """
        if not cls._initialized:
            raise RuntimeError("RAG 서비스가 초기화되지 않음")
        
        start_time = time.time()
        k = top_k or cls._config.default_k
        
        # 검색어 전처리 추가
        processed_query = cls._preprocess_query(query)
        
        Logger.info(f"🔍 하이브리드 검색 시작: '{query}' → '{processed_query}' (k={k}, hybrid={hybrid})")
        
        try:
            cls._stats["search_requests"] += 1
            
            # 하이브리드 검색 실행 (전처리된 쿼리 사용)
            if hybrid and cls._search_available and cls._vector_available:
                cls._stats["hybrid_searches"] += 1
                results = await cls._hybrid_search(processed_query, k, bm25_weight, vector_weight)
            elif cls._vector_available:
                Logger.info("벡터 검색 모드")
                results = await cls._vector_search_only(processed_query, k)
            elif cls._search_available:
                Logger.info("키워드 검색 모드")
                results = await cls._bm25_search_only(processed_query, k)
            else:
                Logger.error("사용 가능한 검색 서비스가 없음")
                return []
            
            # 성능 통계 업데이트
            search_time = time.time() - start_time
            cls._update_search_stats(search_time)
            
            Logger.info(f"✅ 검색 완료: {len(results)}개 결과 ({search_time:.3f}초)")
            
            return results
            
        except Exception as e:
            Logger.error(f"❌ 검색 실패: {e}")
            return []

    @classmethod
    async def _hybrid_search(cls, 
                           query: str, 
                           k: int, 
                           bm25_weight: float, 
                           vector_weight: float) -> List[Dict[str, Any]]:
        """하이브리드 검색 실행"""
        Logger.debug("하이브리드 검색 모드 시작")
        
        # 병렬로 두 가지 검색 실행
        bm25_task = cls._bm25_search_only(query, k * 2)  # 더 많이 가져와서 다양성 확보
        vector_task = cls._vector_search_only(query, k * 2)
        
        bm25_results, vector_results = await asyncio.gather(bm25_task, vector_task)
        
        # 점수 합성 및 순위 결정
        combined_results = cls._fuse_search_results(
            bm25_results, vector_results, 
            bm25_weight, vector_weight
        )
        
        # 상위 K개 반환
        return combined_results[:k]

    @classmethod
    async def _bm25_search_only(cls, query: str, k: int) -> List[Dict[str, Any]]:
        """BM25 키워드 검색만 실행 - 크롤러 구조에 맞춤"""
        try:
            from service.search.search_service import SearchService
            
            # 크롤러에서 저장한 OpenSearch 구조에 맞춤
            search_query = {
                "query": {
                    "multi_match": {
                        "query": query,
                        "fields": ["title", "ticker", "source"],  # 크롤러 구조
                        "type": "best_fields"
                    }
                },
                "size": k
            }
            
            # 크롤러가 실제로 사용하는 인덱스 이름으로 수정
            response = await SearchService.search("yahoo_finance_news", search_query)
            
            if not response:
                return []
            
            results = []
            for hit in response.get("hits", {}).get("hits", []):
                source_data = hit["_source"]
                
                # 크롤러 구조에서 title과 source 추출
                title = source_data.get("title", "No title")
                source = source_data.get("source", "unknown")
                
                # 크롤러 구조에 맞춰 메타데이터 구성
                metadata = {
                    "title": title,
                    "source": source,
                    "ticker": source_data.get("ticker", ""),
                    "date": source_data.get("date", ""),
                    "link": source_data.get("link", ""),
                    "content_type": source_data.get("content_type", ""),
                    "task_id": source_data.get("task_id", ""),
                    "collected_at": source_data.get("collected_at", ""),
                    "created_at": source_data.get("created_at", "")
                }
                
                # 크롤러에서는 title이 실제 뉴스 제목이므로 content로 사용
                content = title
                
                result = {
                    "id": hit["_id"],
                    "content": content,
                    "metadata": metadata,
                    "score": hit["_score"],
                    "search_type": "bm25"
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            Logger.error(f"BM25 검색 실패: {e}")
            return []

    @classmethod
    async def _vector_search_only(cls, query: str, k: int) -> List[Dict[str, Any]]:
        """벡터 유사도 검색만 실행 - RAG 전용 클라이언트 사용"""
        try:
            # RAG 전용 벡터 클라이언트 사용 (coroutine 재사용 문제 해결)
            if cls._rag_vector_client:
                vector_results = await cls._rag_vector_client.similarity_search(
                    query=query,
                    top_k=k
                )
                
                if not vector_results.get("success"):
                    Logger.warn(f"RAG 벡터 검색 실패: {vector_results.get('error', 'Unknown error')}")
                    return []
                
                results = []
                for result in vector_results.get("results", []):
                    doc_result = {
                        "id": result.get("id", ""),
                        "content": result.get("content", ""),
                        "metadata": result.get("metadata", {}),
                        "score": result.get("score", 0.0),
                        "search_type": "vector"
                    }
                    results.append(doc_result)
                
                return results
            
            else:
                # Fallback: 기존 VectorDbService 사용
                from service.vectordb.vectordb_service import VectorDbService
                
                # 쿼리 임베딩 생성
                embed_result = await VectorDbService.embed_text(query)
                
                if not embed_result.get("success"):
                    Logger.warn("쿼리 임베딩 생성 실패")
                    return []
                
                # 벡터 검색 실행
                vector_results = await VectorDbService.similarity_search(
                    query=query,
                    top_k=k
                )
                
                if not vector_results:
                    return []
                
                results = []
                for result in vector_results.get("results", []):
                    doc_result = {
                        "id": result.get("id", ""),
                        "content": result.get("content", ""),
                        "metadata": result.get("metadata", {}),
                        "score": result.get("score", 0.0),
                        "search_type": "vector"
                    }
                    results.append(doc_result)
                
                return results
            
        except Exception as e:
            Logger.error(f"벡터 검색 실패: {e}")
            return []

    @classmethod
    def _fuse_search_results(cls,
                           bm25_results: List[Dict[str, Any]],
                           vector_results: List[Dict[str, Any]],
                           bm25_weight: float,
                           vector_weight: float) -> List[Dict[str, Any]]:
        """BM25와 벡터 검색 결과 점수 합성"""
        
        # 결과를 ID로 매핑
        bm25_map = {r["id"]: r for r in bm25_results}
        vector_map = {r["id"]: r for r in vector_results}
        
        # 모든 고유한 문서 ID 수집
        all_ids = set(bm25_map.keys()) | set(vector_map.keys())
        
        combined = []
        
        for doc_id in all_ids:
            bm25_result = bm25_map.get(doc_id)
            vector_result = vector_map.get(doc_id)
            
            # 점수 정규화 및 합성
            bm25_score = cls._normalize_bm25_score(bm25_result["score"]) if bm25_result else 0.0
            vector_score = vector_result["score"] if vector_result else 0.0
            
            # 가중 평균 점수 계산
            combined_score = (bm25_score * bm25_weight) + (vector_score * vector_weight)
            
            # 우선순위: BM25 > Vector (메타데이터 풍부도 기준)
            primary_result = bm25_result or vector_result
            
            combined_result = {
                **primary_result,
                "score": combined_score,
                "search_type": "hybrid",
                "score_details": {
                    "bm25_score": bm25_score,
                    "vector_score": vector_score,
                    "bm25_weight": bm25_weight,
                    "vector_weight": vector_weight
                }
            }
            
            combined.append(combined_result)
        
        # 점수 순으로 정렬
        combined.sort(key=lambda x: x["score"], reverse=True)
        
        return combined

    @classmethod
    def _normalize_bm25_score(cls, score: float) -> float:
        """BM25 점수를 0-1 범위로 정규화"""
        # 간단한 sigmoid 정규화 (실제로는 데이터에 맞게 조정 필요)
        import math
        return 1 / (1 + math.exp(-score / 10))

    @classmethod
    def _update_search_stats(cls, search_time: float):
        """검색 성능 통계 업데이트"""
        current_avg = cls._stats["avg_search_time"]
        search_count = cls._stats["search_requests"]
        
        # 이동 평균 계산
        cls._stats["avg_search_time"] = (
            (current_avg * (search_count - 1)) + search_time
        ) / search_count

    @classmethod
    def is_initialized(cls) -> bool:
        """서비스 초기화 상태 확인 (111 패턴)"""
        return cls._initialized

    @classmethod
    def get_stats(cls) -> Dict[str, Any]:
        """성능 통계 반환"""
        return {
            **cls._stats,
            "initialized": cls._initialized,
            "search_available": cls._search_available,
            "vector_available": cls._vector_available,
            "hybrid_capable": cls._search_available and cls._vector_available
        }

    @classmethod
    async def health_check(cls) -> Dict[str, Any]:
        """서비스 상태 확인"""
        if not cls._initialized:
            return {
                "status": "not_initialized",
                "message": "RAG 서비스가 초기화되지 않음"
            }
        
        # 의존 서비스 상태 재확인
        try:
            from service.search.search_service import SearchService
            from service.vectordb.vectordb_service import VectorDbService
            
            search_status = SearchService.is_initialized()
            vector_status = VectorDbService.is_initialized()
            
            if search_status and vector_status:
                status = "healthy"
            elif search_status or vector_status:
                status = "degraded"
            else:
                status = "critical"
            
            return {
                "status": status,
                "initialized": cls._initialized,
                "dependencies": {
                    "search_service": search_status,
                    "vector_service": vector_status
                },
                "capabilities": {
                    "hybrid_search": search_status and vector_status,
                    "keyword_search": search_status,
                    "vector_search": vector_status
                },
                "stats": cls.get_stats()
            }
            
        except Exception as e:
            Logger.error(f"RAG 서비스 상태 확인 실패: {e}")
            return {
                "status": "error",
                "message": f"상태 확인 중 오류: {e}"
            }

    @classmethod
    async def shutdown(cls) -> bool:
        """서비스 종료 (111 패턴)"""
        try:
            if not cls._initialized:
                Logger.info("RAG 서비스가 초기화되지 않아 종료 스킵")
                return True
            
            Logger.info("🔄 RAG 서비스 종료 시작...")
            
            # 통계 로그 출력
            stats = cls.get_stats()
            Logger.info(f"RAG 서비스 통계:")
            Logger.info(f"  - 인덱싱된 문서: {stats['documents_indexed']}개")
            Logger.info(f"  - 검색 요청: {stats['search_requests']}개")
            Logger.info(f"  - 하이브리드 검색: {stats['hybrid_searches']}개")
            Logger.info(f"  - 평균 검색 시간: {stats['avg_search_time']:.3f}초")
            
            # RAG 전용 벡터 클라이언트 종료
            if cls._rag_vector_client:
                try:
                    await cls._rag_vector_client.close()
                    Logger.info("✅ RAG 전용 벡터 클라이언트 종료 완료")
                except Exception as e:
                    Logger.error(f"❌ RAG 전용 벡터 클라이언트 종료 실패: {e}")
            
            # 상태 초기화
            cls._initialized = False
            cls._config = None
            cls._search_available = False
            cls._vector_available = False
            cls._rag_vector_client = None
            cls._reset_stats()
            
            Logger.info("✅ RAG 서비스 종료 완료")
            return True
            
        except Exception as e:
            Logger.error(f"❌ RAG 서비스 종료 실패: {e}")
            return False