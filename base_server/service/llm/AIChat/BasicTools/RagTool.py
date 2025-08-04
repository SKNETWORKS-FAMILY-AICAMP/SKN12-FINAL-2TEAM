import os
import json
from typing import Optional, List, Dict, Any
from service.llm.AIChat.BaseFinanceTool import BaseFinanceTool
from pydantic import BaseModel, Field

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
    
    def __init__(self, ai_chat_service):
        from service.llm.AIChat_service import AIChatService
        if not isinstance(ai_chat_service, AIChatService):
            raise TypeError("Expected AIChatService instance")
        self.ai_chat_service = ai_chat_service
        
        # 벡터 DB 초기화 (예: ChromaDB, Faiss, Pinecone 등)
        self._initialize_vector_db()
    
    def _initialize_vector_db(self):
        """벡터 데이터베이스 초기화"""
        try:
            # 임베딩 모델 설정 (예: OpenAI embeddings, SentenceTransformers 등)
            from sentence_transformers import SentenceTransformer
            self.embedding_model = SentenceTransformer('sentence-transformers/all-MiniLM-L6-v2')
            
            # 벡터 DB 연결 설정 (예시: ChromaDB)
            import chromadb
            self.chroma_client = chromadb.PersistentClient(path="./vector_db")
            self.collection = self.chroma_client.get_or_create_collection(
                name="financial_news_collection",
                metadata={"hnsw:space": "cosine"}
            )
            
        except ImportError as e:
            print(f"⚠️  벡터 DB 라이브러리가 설치되지 않았습니다: {e}")
            self.embedding_model = None
            self.collection = None
        except Exception as e:
            print(f"⚠️  벡터 DB 초기화 오류: {e}")
            self.embedding_model = None
            self.collection = None

    def _get_embedding(self, text: str) -> List[float]:
        """텍스트를 벡터로 변환"""
        if self.embedding_model is None:
            return []
        
        try:
            embedding = self.embedding_model.encode(text).tolist()
            return embedding
        except Exception as e:
            print(f"임베딩 생성 오류: {e}")
            return []

    def _search_vector_db(self, query: str, k: int, threshold: float) -> List[Dict[str, Any]]:
        """벡터 DB에서 유사 문서 검색"""
        if self.collection is None:
            return []
        
        try:
            # 쿼리를 벡터로 변환
            query_embedding = self._get_embedding(query)
            if not query_embedding:
                return []
            
            # 벡터 DB에서 검색
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=k,
                include=["documents", "metadatas", "distances"]
            )
            
            documents = []
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
            
            return documents
            
        except Exception as e:
            print(f"벡터 DB 검색 오류: {e}")
            return []

    def _fallback_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """벡터 DB가 없을 때 대체 검색 (예: 데이터베이스에서 키워드 검색)"""
        # 실제 구현에서는 데이터베이스에서 뉴스 데이터를 키워드 기반으로 검색
        # 여기서는 예시 데이터를 반환
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
        return fallback_docs[:k]

    def get_data(self, **kwargs) -> RagOutput:
        try:
            input_data = RagInput(**kwargs)
        except Exception as e:
            return RagOutput(agent="error", summary=f"❌ 매개변수 오류: {e}")

        try:
            # 벡터 DB에서 검색
            documents = self._search_vector_db(
                input_data.query, 
                input_data.k, 
                input_data.threshold
            )
            
            # 벡터 DB 검색 결과가 없으면 대체 검색 수행
            if not documents:
                documents = self._fallback_search(input_data.query, input_data.k)
            
            if not documents:
                return RagOutput(
                    agent="RagTool", 
                    summary=f"📭 '{input_data.query}'에 대한 관련 문서를 찾을 수 없습니다."
                )
            
            # 요약 생성
            summary_lines = [f"🔍 '{input_data.query}' 검색 결과 {len(documents)}건:"]
            for i, doc in enumerate(documents, 1):
                similarity_percent = int(doc['similarity'] * 100)
                summary_lines.append(
                    f"{i}. {doc['title']} (유사도: {similarity_percent}%) - {doc['source']}"
                )
            
            summary = "\n".join(summary_lines)
            
            # 문서 리스트 정리 (응답에 포함할 핵심 정보만)
            document_list = [
                {
                    "title": doc["title"],
                    "content": doc["content"][:200] + "..." if len(doc["content"]) > 200 else doc["content"],
                    "similarity": doc["similarity"],
                    "source": doc["source"]
                }
                for doc in documents
            ]
            
            return RagOutput(
                agent="RagTool",
                summary=summary,
                documents=document_list,
                data=documents  # 전체 상세 데이터
            )
            
        except Exception as e:
            return RagOutput(
                agent="error", 
                summary=f"🔧 RAG 검색 오류: {e}"
            )

    def add_document(self, content: str, metadata: Dict[str, Any]) -> bool:
        """벡터 DB에 새 문서 추가"""
        if self.collection is None:
            print("⚠️  벡터 DB가 초기화되지 않았습니다.")
            return False
        
        try:
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
            
            return True
            
        except Exception as e:
            print(f"문서 추가 오류: {e}")
            return False
