import os
import json
import time
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid
import logging
import datetime
import contextvars
import re
from typing import Optional, List, Dict, Any
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool
from service.rag.rag_config import RagConfig
from service.rag.rag_service import RagService
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
        
        class OnlyTestLogFilter(logging.Filter):
            def filter(self, record: logging.LogRecord) -> bool:
                try:
                    msg = record.getMessage()
                except Exception:
                    msg = str(record.msg)
                return "log.test" in msg

        handler.addFilter(OnlyTestLogFilter())
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

def _run_async(coro):
    """Run coroutine safely from sync context, even if an event loop is already running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return asyncio.run(coro)
    # If we're already inside an event loop, run in a separate thread with its own loop
    def runner():
        return asyncio.run(coro)
    with ThreadPoolExecutor(max_workers=1) as ex:
        future = ex.submit(runner)
        return future.result()

class RagInput(BaseModel):
    query: str = Field(..., description="검색할 질문 또는 키워드. 영어로만. (예: 'finance', 'TSLA')")
    k: int = Field(5, description="검색할 문서 개수 (기본값: 5)")
    threshold: float = Field(0.1, description="유사도 임계값 (기본값: 0.1)")

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
        # 우선순위: 전달된 rag_config → 서비스 보관 rag_config → (나중에) 전역 RAG 설정
        self.rag_config: Optional[RagConfig] = rag_config or getattr(ai_chat_service, 'rag_config', None)
        
        # RAG 서비스 초기화 (OpenSearch/VectorDbService 기반)
        try:
            _emit_log(logging.getLogger(__name__), logging.INFO, "rag.service.init.start")
            if not RagService.is_initialized():
                # 필요한 경우에만 설정을 구성 (지연 생성)
                config_candidate = self.rag_config or getattr(ai_chat_service, 'rag_config', None)
                if config_candidate is None:
                    # 환경변수에서 자격 증명 유무 확인 후 안전하게 구성
                    aws_key = os.getenv('AWS_ACCESS_KEY_ID', os.getenv('AWS_ACCESS_KEY', '')).strip()
                    aws_secret = os.getenv('AWS_SECRET_ACCESS_KEY', '').strip()
                    kb_id = os.getenv('RAG_KB_ID', '').strip()
                    enable_vector = bool(aws_key and aws_secret and kb_id)
                    try:
                        self.rag_config = RagConfig(
                            aws_access_key_id=aws_key,
                            aws_secret_access_key=aws_secret,
                            knowledge_base_id=kb_id,
                            enable_vector_db=enable_vector
                        )
                    except Exception:
                        # 검증 실패 시 로컬/BM25만 사용하도록 비활성화
                        self.rag_config = RagConfig(enable_vector_db=False)
                else:
                    # 제공된 설정에서 자격증명 미비 시 벡터 DB 비활성화로 강등
                    try:
                        if getattr(config_candidate, 'enable_vector_db', True) and (
                            not getattr(config_candidate, 'aws_access_key_id', '').strip() or
                            not getattr(config_candidate, 'aws_secret_access_key', '').strip() or
                            not getattr(config_candidate, 'knowledge_base_id', '').strip()
                        ):
                            self.rag_config = config_candidate.model_copy(update={"enable_vector_db": False})
                        else:
                            self.rag_config = config_candidate
                    except Exception:
                        # 어떤 이유로든 복사 실패 시 안전 기본값
                        self.rag_config = RagConfig(enable_vector_db=False)
                # 최종 구성 확인용 디버그
                try:
                    from service.rag.rag_service import RagService as _RS
                    _ = self.rag_config.dict() if hasattr(self.rag_config, 'dict') else self.rag_config.__dict__
                    _emit_log(logging.getLogger(__name__), logging.DEBUG, "rag.config.active", {
                        "enable_vector_db": str(self.rag_config.enable_vector_db),
                        "kb_id_set": str(bool(getattr(self.rag_config, 'knowledge_base_id', ''))),
                        "region": getattr(self.rag_config, 'region_name', ''),
                    })
                except Exception:
                    pass
                RagService.init(self.rag_config)
            _emit_log(logging.getLogger(__name__), logging.INFO, "rag.service.init.done")
        except Exception as e:
            _emit_log(logging.getLogger(__name__), logging.ERROR, "rag.service.init.error", {"message": str(e)}, exc_info=True)

        # 보장: self.rag_config가 항상 존재하도록 최종 확인
        try:
            if self.rag_config is None:
                from service.rag.rag_service import RagService as _RS
                self.rag_config = _RS.get_config() or RagConfig(enable_vector_db=False)
        except Exception:
            self.rag_config = RagConfig(enable_vector_db=False)
        
        # 더 이상 로컬 Chroma 초기화 사용 안 함
        self.embedding_model = None
        self.collection = None
    
    def _initialize_vector_db(self):
        """이전 Chroma 초기화 메서드(호환성 유지). 현재는 비활성."""
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
            # 가독성 높은 시작 디버그
            try:
                logger.debug(
                    f"log.test ragtool.start query='{str(kwargs.get('query', ''))[:80]}' k={kwargs.get('k', 5)} threshold={kwargs.get('threshold', 0.7)} request_id={request_id}"
                )
            except Exception:
                pass
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
            # RAG 서비스 검색 (OpenSearch/VectorDbService 기반)
            used_fallback = False
            search_start = time.perf_counter()
            try:
                results = _run_async(RagService.retrieve(
                    query=input_data.query,
                    top_k=input_data.k,
                    hybrid=True
                ))
            except Exception as e:
                _emit_log(
                    logger=logger,
                    level=logging.ERROR,
                    event="rag.service.search.error",
                    fields={"message": str(e)},
                    exc_info=True,
                )
                results = []
            search_elapsed = int((time.perf_counter() - search_start) * 1000)
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="rag.service.search",
                fields={"returned": len(results) if results else 0, "elapsed_ms": search_elapsed},
            )
            try:
                logger.debug(
                    f"log.test ragtool.search returned={len(results) if results else 0} elapsed_ms={search_elapsed}"
                )
            except Exception:
                pass

            # 결과 정규화 및 임계값 필터링
            documents = []
            if results:
                for idx, r in enumerate(results):
                    md = r.get("metadata", {})
                    score = float(r.get("score", 0.0))
                    doc = {
                        "content": r.get("content", ""),
                        "similarity": round(score, 3),
                        "metadata": md,
                        "source": md.get("source", "unknown"),
                        "title": md.get("title", md.get("ticker", "제목 없음")),
                        "date": md.get("date", "날짜 없음"),
                    }
                    documents.append(doc)
                    _emit_log(
                        logger=logger,
                        level=logging.DEBUG,
                        event="rag.service.doc",
                        fields={
                            "rank": idx + 1,
                            "title": doc["title"],
                            "source": doc["source"],
                            "score": doc["similarity"],
                        },
                    )
                # 상위 결과 요약 디버그 출력 (가독성)
                try:
                    preview_count = min(5, len(documents))
                    for i in range(preview_count):
                        d = documents[i]
                        title_preview = (d["title"] or "")[:80]
                        logger.debug(
                            f"log.test ragtool.result#{i+1} score={d['similarity']:.3f} source='{d['source']}' title='{title_preview}'"
                        )
                except Exception:
                    pass

            kept_docs = []
            dropped = 0
            for d in documents:
                if d["similarity"] >= input_data.threshold:
                    kept_docs.append(d)
                else:
                    dropped += 1
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="filter.apply",
                fields={"threshold": input_data.threshold, "kept": len(kept_docs), "dropped": dropped},
            )
            documents = kept_docs

            # 서비스 결과 없고 폴백 허용 시
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
                try:
                    logger.debug(f"log.test ragtool.fallback used=True elapsed_ms={fb_elapsed_ms}")
                except Exception:
                    pass
            
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
            
            # 요약 생성: "**제목** - 출처, 날짜" 형식만 반환
            sum_start = time.perf_counter()
            formatted_lines: List[str] = []

            def _clean_text(value: str) -> str:
                if not value:
                    return ""
                text = str(value)
                # 실개행/이스케이프 개행 모두 공백으로 정리
                text = text.replace("\n", " ").replace("\\n", " ").replace("\r", " ")
                # 흔한 메타데이터 꼬리 제거
                text = re.sub(r"(\\?\"metadata\\?\":.*)$", "", text)
                text = re.sub(r"(Published on:.*)$", "", text, flags=re.IGNORECASE)
                # 공백 축소 및 양끝 따옴표 제거
                text = re.sub(r"\s+", " ", text).strip().strip("'\"")
                return text

            for doc in documents:
                md = doc.get("metadata", {})
                raw_title = md.get("title_en") or (doc.get("title") or "")
                title = _clean_text(raw_title)
                source = (doc.get("source") or md.get("source") or "").strip() or "Unknown"
                date = (md.get("date") or md.get("published_at") or "").strip()

                # 항목은 제목/출처/(옵션)날짜를 줄바꿈으로 구성하고, 항목 간에는 빈 줄 추가
                formatted_lines.append(title)
                formatted_lines.append(f"출처 : {source}")
                if date:
                    formatted_lines.append(f"날짜 : {date}")
                formatted_lines.append("")

            # 맨 끝 공백 줄 제거
            while formatted_lines and formatted_lines[-1] == "":
                formatted_lines.pop()

            # 헤더는 굵은 글씨로, 문장형 마침표 포함
            header = f"**{input_data.query} 관련 최신 뉴스 {len(documents)}건입니다.**"
            summary = header + "\n\n" + "\n".join(formatted_lines)
            sum_elapsed_ms = int((time.perf_counter() - sum_start) * 1000)
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="summary.done",
                fields={"lines": len(formatted_lines), "elapsed_ms": sum_elapsed_ms},
            )
            try:
                logger.debug(f"log.test ragtool.summary lines={len(formatted_lines)} elapsed_ms={sum_elapsed_ms}")
            except Exception:
                pass
            
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
            try:
                logger.debug(
                    f"log.test ragtool.return documents={len(document_list)} used_fallback={used_fallback} total_elapsed_ms={total_elapsed_ms}"
                )
            except Exception:
                pass
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
        """문서 추가 (현재 구현에서는 RAG 서비스 경로를 사용하도록 변경 권장)."""
        logger = logging.getLogger(__name__)
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
            # 간단히 성공 처리 (Chroma 제거 후, 실제 저장은 상위 파이프라인에서 수행)
            _emit_log(
                logger=logger,
                level=logging.INFO,
                event="document.add.done",
                fields={"note": "Use RagService.add_documents in service layer"},
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
