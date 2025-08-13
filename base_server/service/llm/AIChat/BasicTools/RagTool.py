import os
import json
import time
import uuid
import logging
import datetime
import contextvars
from typing import Optional, List, Dict, Any
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool
from service.rag.rag_config import RagConfig
from pydantic import BaseModel, Field

# =========================
# Logging helpers (RAG)
# =========================
_request_id_var: contextvars.ContextVar[str] = contextvars.ContextVar("request_id", default="")
_RAG_LOG_FORMAT = "plain"
_RAG_LOG_CONTENT_MAXLEN = 200

def init_rag_logging() -> None:
    """Initialize structured logging for RAG once (idempotent)."""
    global _RAG_LOG_FORMAT, _RAG_LOG_CONTENT_MAXLEN
    level_name = os.getenv("RAG_LOG_LEVEL", "INFO").upper()
    level = getattr(logging, level_name, logging.INFO)
    _RAG_LOG_FORMAT = os.getenv("RAG_LOG_FORMAT", "plain").lower()
    try:
        _RAG_LOG_CONTENT_MAXLEN = int(os.getenv("RAG_LOG_CONTENT_MAXLEN", "200"))
    except Exception:
        _RAG_LOG_CONTENT_MAXLEN = 200

    logger = logging.getLogger(__name__)
    if getattr(logger, "_rag_initialized", False):
        return
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setLevel(level)
        handler.setFormatter(logging.Formatter("%(message)s"))
        logger.addHandler(handler)
    logger.propagate = False
    setattr(logger, "_rag_initialized", True)

def _now_ts() -> str:
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"

def _set_request_id(request_id: str) -> None:
    _request_id_var.set(request_id)

def _reset_request_id() -> None:
    try:
        _request_id_var.set("")
    except Exception:
        pass

def _truncate_text(text: str) -> str:
    if text is None:
        return ""
    if len(text) <= _RAG_LOG_CONTENT_MAXLEN:
        return text
    return text[:_RAG_LOG_CONTENT_MAXLEN] + "..."

def _emit_log(logger: logging.Logger, level: int, event: str, fields: Optional[Dict[str, Any]] = None, exc_info: bool = False) -> None:
    payload: Dict[str, Any] = {
        "level": logging.getLevelName(level),
        "ts": _now_ts(),
        "request_id": _request_id_var.get() or None,
        "event": event,
    }
    if fields:
        payload.update(fields)

    if _RAG_LOG_FORMAT == "json":
        try:
            message = json.dumps({k: v for k, v in payload.items() if v is not None}, ensure_ascii=False)
        except Exception:
            message = json.dumps({"level": payload.get("level"), "ts": payload.get("ts"), "event": event}, ensure_ascii=False)
    else:
        # plain key=value with quoted strings
        def _fmt_val(v: Any) -> str:
            if isinstance(v, (int, float)):
                return str(v)
            if isinstance(v, bool):
                return "true" if v else "false"
            if v is None:
                return "null"
            s = str(v)
            s = s.replace('"', '\\"')
            return f'"{s}"'
        parts = [
            f"level={payload['level']}",
            f"ts={payload['ts']}",
        ]
        if payload.get("request_id"):
            parts.append(f"request_id={payload['request_id']}")
        parts.append(f"event={_fmt_val(event)}")
        for k, v in payload.items():
            if k in ("level", "ts", "request_id", "event"):
                continue
            parts.append(f"{k}={_fmt_val(v)}")
        message = " ".join(parts)
    logger.log(level, message, exc_info=exc_info)

class RagInput(BaseModel):
    query: str = Field(..., description="검색할 질문 또는 키워드 (예: '금리 정책', 'ESG 투자')")
    k: int = Field(5, description="검색할 문서 개수 (기본값: 5)")
    threshold: float = Field(0.7, description="유사도 임계값 (기본값: 0.7)")

class RagOutput(BaseModel):
    agent: str
    summary: str
    documents: Optional[List[Dict[str, Any]]] = None
    data: Optional[Any] = None

    def __init__(
        self,
        agent: str,
        summary: str,
        documents: Optional[List[Dict[str, Any]]] = None,
        data: Optional[Any] = None,
    ):
        super().__init__(
            agent=agent,
            summary=summary,
            documents=documents,
            data=data,
        )

class RagTool(BaseFinanceTool):
    
    def __init__(self, ai_chat_service, rag_config: Optional[RagConfig] = None):
        init_rag_logging()
        logger = logging.getLogger(__name__)
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        self.ai_chat_service = ai_chat_service
        
        # RAG 설정 (매개변수 → 서비스 → 기본값 순서로 우선순위)
        self.rag_config = rag_config or getattr(ai_chat_service, 'rag_config', None) or RagConfig()
        
        # 벡터 DB 초기화
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """벡터 데이터베이스 초기화"""
        logger = logging.getLogger(__name__)
        try:
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="vector.db.init.start",
                fields={
                    "enable_vector_db": getattr(self.rag_config, 'enable_vector_db', None),
                    "embedding_model": getattr(self.rag_config, 'embedding_model', None),
                    "vector_db_path": getattr(self.rag_config, 'vector_db_path', None),
                    "collection_name": getattr(self.rag_config, 'collection_name', None),
                },
            )
            if not self.rag_config.enable_vector_db:
                self.embedding_model = None
                self.collection = None
                _emit_log(
                    logger=logger,
                    level=logging.INFO,
                    event="vector.db.init.skipped",
                    fields={"reason": "disabled by config"},
                )
                return
                
            # 임베딩 모델 설정
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer(self.rag_config.embedding_model)
            
            # 벡터 DB 연결 설정
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path=self.rag_config.vector_db_path)
            self.collection = self.chroma_client.get_or_create_collection(
                name=self.rag_config.collection_name,
                metadata={"hnsw:space": "cosine"}
            )
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="vector.db.init.done",
                fields={
                    "enable_vector_db": True,
                    "embedding_model": self.rag_config.embedding_model,
                    "vector_db_path": self.rag_config.vector_db_path,
                    "collection_name": self.rag_config.collection_name,
                },
            )
            
        except ImportError as e:
            _emit_log(
                logger=logger,
                level=logging.ERROR,
                event="vector.db.init.error",
                fields={"message": f"벡터 DB 라이브러리가 설치되지 않았습니다: {e}"},
                exc_info=True,
            )
            self.embedding_model = None
            self.collection = None
        except Exception as e:
            _emit_log(
                logger=logger,
                level=logging.ERROR,
                event="vector.db.init.error",
                fields={"message": f"벡터 DB 초기화 오류: {e}"},
                exc_info=True,
            )
            self.embedding_model = None
            self.collection = None

    def _get_embedding(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환"""
        logger = logging.getLogger(__name__)
        if self.embedding_model is None:
            _emit_log(
                logger=logger,
                level=logging.WARNING,
                event="embedding.skipped",
                fields={"reason": "embedding model not initialized"},
            )
            return []
        
        try:
            start_t = time.perf_counter()
            preview = _truncate_text(text)
            _emit_log(
                logger=logger,
                level=logging.DEBUG,
                event="embedding.start",
                fields={
                    "input_length": len(text),
                    "preview": preview,
                },
            )
            embedding = self.embedding_model.encode(text).tolist()
            elapsed_ms = int((time.perf_counter() - start_t) * 1000)
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="embedding.done",
                fields={
                    "dim": len(embedding) if isinstance(embedding, list) else 0,
                    "elapsed_ms": elapsed_ms,
                },
            )
            return embedding
        except Exception as e:
            _emit_log(
                logger=logger,
                level=logging.ERROR,
                event="embedding.error",
                fields={"message": f"임베딩 생성 오류: {e}"},
                exc_info=True,
            )
            return []

    def _search_vector_db(self, query: str, k: int, threshold: float) -> List[Dict[str, Any]]:
        """벡터 DB에서 유사 문서 검색"""
        logger = logging.getLogger(__name__)
        if self.collection is None:
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="vector.search.skipped",
                fields={"reason": "vector DB collection not initialized"},
            )
            return []
        
        try:
            # 쿼리를 벡터로 변환
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="vector.search.start",
                fields={
                    "query": _truncate_text(query),
                    "k": k,
                    "threshold": threshold,
                },
            )
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return []
            
            # 벡터 DB에서 검색
            q_start_t = time.perf_counter()
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            q_elapsed_ms = int((time.perf_counter() - q_start_t) * 1000)
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="vector.search",
                fields={
                    "k": k,
                    "returned": len(results['documents'][0]) if results.get('documents') and results['documents'] and results['documents'][0] else 0,
                    "elapsed_ms": q_elapsed_ms,
                },
            )
            
            documents = []
            below_threshold = 0
            filter_start = time.perf_counter()
            if results['documents'] and results['documents'][0]:
                for i, doc in enumerate(results['documents'][0]):
                    distance = results['distances'][0][i] if results['distances'] else 1.0
                    similarity = 1 - distance  # cosine distance를 similarity로 변환
                    
                    # 임계값 이상인 문서만 포함
                    if similarity >= threshold:
                        metadata = results['metadatas'][0][i] if results['metadatas'] else {}
                        documents.append({
                            "content": doc,
                            "similarity": round(similarity, 3),
                            "metadata": metadata,
                            "source": metadata.get("source", "unknown"),
                            "title": metadata.get("title", "제목 없음"),
                            "date": metadata.get("date", "날짜 없음")
                        })
                        _emit_log(
                            logger=logger,
                            level=logging.DEBUG,
                            event="vector.search.doc",
                            fields={
                                "rank": i + 1,
                                "title": documents[-1]["title"],
                                "source": documents[-1]["source"],
                                "similarity": round(similarity, 3),
                                "distance": round(distance, 3),
                            },
                        )
                    else:
                        below_threshold += 1
            filter_elapsed_ms = int((time.perf_counter() - filter_start) * 1000)
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="filter.apply",
                fields={
                    "threshold": threshold,
                    "kept": len(documents),
                    "dropped": below_threshold,
                    "elapsed_ms": filter_elapsed_ms,
                },
            )
            
            return documents
            
        except Exception as e:
            _emit_log(
                logger=logger,
                level=logging.ERROR,
                event="vector.search.error",
                fields={"message": f"벡터 DB 검색 오류: {e}"},
                exc_info=True,
            )
            return []

    def _fallback_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """벡터 DB가 없을 때 대체 검색 (예: 데이터베이스에서 키워드 검색)"""
        logger = logging.getLogger(__name__)
        # 실제 구현에서는 데이터베이스에서 뉴스 데이터를 키워드 기반으로 검색
        # 여기서는 예시 데이터를 반환
        _emit_log(
            logger=logger,
            level=logging.WARNING,
            event="fallback.used",
            fields={"reason": "vector search empty → fallback enabled"},
        )
        fallback_docs = [
            {
                "content": f"'{query}'와 관련된 금융 뉴스 내용입니다. 실제 구현에서는 데이터베이스에서 검색된 결과가 표시됩니다.",
                "similarity": 0.8,
                "metadata": {
                    "source": "fallback_search",
                    "title": f"{query} 관련 뉴스",
                    "date": "2024-01-01"
                },
                "source": "fallback_search",
                "title": f"{query} 관련 뉴스", 
                "date": "2024-01-01"
            }
        ]
        docs = fallback_docs[:k]
        _emit_log(
            logger=logger,
            level=logging.INFO,
            event="fallback.return",
            fields={"returned": len(docs)},
        )
        return docs

    def get_data(self, **kwargs) -> RagOutput:
        logger = logging.getLogger(__name__)
        request_id = str(uuid.uuid4())
        _set_request_id(request_id)
        total_start = time.perf_counter()
        try:
            input_data = RagInput(**kwargs)
        except Exception as e:
            _emit_log(
                logger=logger,
                level=logging.ERROR,
                event="rag.param.error",
                fields={"message": f"매개변수 오류: {e}"},
                exc_info=True,
            )
            return RagOutput(agent="error", summary=f"❌ 매개변수 오류: {e}")

        try:
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="RAG start",
                fields={
                    "query": _truncate_text(input_data.query),
                    "k": input_data.k,
                    "threshold": input_data.threshold,
                    "request_id": request_id,
                },
            )
            # 벡터 DB에서 검색
            used_fallback = False
            documents = self._search_vector_db(
                input_data.query, 
                input_data.k, 
                input_data.threshold
            )
            
            # 벡터 DB 검색 결과가 없으면 대체 검색 수행
            if not documents and self.rag_config.enable_fallback_search:
                fb_start = time.perf_counter()
                documents = self._fallback_search(input_data.query, input_data.k)
                fb_elapsed_ms = int((time.perf_counter() - fb_start) * 1000)
                _emit_log(
                    logger=logger,
                    level=logging.INFO,
                    event="fallback.done",
                    fields={"returned": len(documents), "elapsed_ms": fb_elapsed_ms},
                )
                used_fallback = True
            
            if not documents:
                total_elapsed_ms = int((time.perf_counter() - total_start) * 1000)
                _emit_log(
                    logger=logger,
                    level=logging.INFO,
                    event="RAG return",
                    fields={
                        "documents": 0,
                        "used_fallback": used_fallback,
                        "total_elapsed_ms": total_elapsed_ms,
                    },
                )
                return RagOutput(
                    agent="RagTool", 
                    summary=f"📭 '{input_data.query}'에 대한 관련 문서를 찾을 수 없습니다."
                )
            
            # 요약 생성
            sum_start = time.perf_counter()
            summary_lines = [f"🔍 '{input_data.query}' 검색 결과 {len(documents)}건:"]
            for i, doc in enumerate(documents, 1):
                similarity_percent = int(doc['similarity'] * 100)
                summary_lines.append(
                    f"{i}. {doc['title']} (유사도: {similarity_percent}%) - {doc['source']}"
                )
            
            summary = "\n".join(summary_lines)
            sum_elapsed_ms = int((time.perf_counter() - sum_start) * 1000)
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="summary.done",
                fields={"lines": len(summary_lines), "elapsed_ms": sum_elapsed_ms},
            )
            
            # 문서 리스트 정리 (응답에 포함할 핵심 정보만)
            max_length = self.rag_config.max_content_length
            document_list = [
                {
                    "title": doc["title"],
                    "content": doc["content"][:max_length] + "..." if len(doc["content"]) > max_length else doc["content"],
                    "similarity": doc["similarity"],
                    "source": doc["source"]
                }
                for doc in documents
            ]
            
            total_elapsed_ms = int((time.perf_counter() - total_start) * 1000)
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="RAG return",
                fields={
                    "documents": len(document_list),
                    "used_fallback": used_fallback,
                    "total_elapsed_ms": total_elapsed_ms,
                },
            )
            return RagOutput(
                agent="RagTool",
                summary=summary,
                documents=document_list,
                data=documents  # 전체 상세 데이터
            )
            
        except Exception as e:
            _emit_log(
                logger=logger,
                level=logging.ERROR,
                event="rag.error",
                fields={"message": f"RAG 검색 오류: {e}"},
                exc_info=True,
            )
            return RagOutput(
                agent="error", 
                summary=f"🔧 RAG 검색 오류: {e}"
            )
        finally:
            _reset_request_id()

    def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """벡터 DB에 새 문서 추가"""
        logger = logging.getLogger(__name__)
        if self.collection is None:
            _emit_log(
                logger=logger,
                level=logging.WARNING,
                event="document.add.skipped",
                fields={"reason": "vector DB not initialized"},
            )
            return False
        
        try:
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="document.add.start",
                fields={
                    "title": metadata.get("title"),
                    "source": metadata.get("source"),
                    "date": metadata.get("date"),
                },
            )
            # 문서를 벡터로 변환
            embedding = self._get_embedding(content)
            if not embedding:
                return False
            
            # 고유 ID 생성
            doc_id = f"doc_{hash(content)}"
            
            # 벡터 DB에 추가
            self.collection.add(
                embeddings=[embedding],
                documents=[content],
                metadatas=[metadata],
                ids=[doc_id]
            )
            
            _emit_log(
                logger=logger,
                level=logging.DEBUG,
                event="document.add.embedded",
                fields={"dim": len(embedding), "doc_id": doc_id},
            )
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="document.add.done",
                fields={"doc_id": doc_id},
            )
            return True
            
        except Exception as e:
            _emit_log(
                logger=logger,
                level=logging.ERROR,
                event="document.add.error",
                fields={"message": f"문서 추가 오류: {e}"},
                exc_info=True,
            )
            return False
