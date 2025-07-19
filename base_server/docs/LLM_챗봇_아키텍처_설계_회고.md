# 📝 21주차 학습 회고 - LLM 챗봇 아키텍처 설계

## 1. LLM 기반 챗봇 히스토리 저장 아키텍처 설계

### 🤔 의사결정 과정

#### 고민했던 선택지들

| 선택지 | 장점 | 단점 | 판단 |
|--------|------|------|------|
| **Redis 단독** | • 초고속 읽기/쓰기 (메모리 기반)<br>• 간단한 아키텍처 | • 대용량 저장 시 월 수백만원 비용<br>• 영속성 리스크 | ❌ 비용 효율성 너무 낮음 |
| **MySQL 단독** | • 영구 저장 보장<br>• 복잡한 쿼리 가능 | • 실시간 채팅 응답성 저하<br>• 높은 동시성 시 병목 | ❌ 사용자 경험 희생 |
| **Redis + MySQL** | • 실시간성과 영속성 확보<br>• 기존 인프라 활용 | • 데이터 동기화 필요<br>• 운영 복잡도 증가 | ✅ 가장 균형잡힌 선택 |
| **Redis + Elasticsearch** | • 강력한 full-text 검색<br>• 분석 대시보드 | • 새 인프라 도입 필요<br>• 라이선스 비용 | ❌ 현재 규모에 오버엔지니어링 |

#### 🎯 최종 선택: Redis + MySQL 하이브리드

**선택 이유:**
1. base_server가 이미 두 시스템을 안정적으로 운영 중
2. Hot/Cold 데이터 분리로 비용과 성능 최적화
3. 팀이 이미 숙련된 기술로 빠른 구현 가능
4. 필요시 OpenSearch 추가 등 점진적 확장 용이

### 💻 구현 코드 예시

#### 1. ChatTemplateImpl 확장 (Redis + MySQL 하이브리드)
```python
# base_server/template/chat/chat_template_impl.py

from template.base.base_template import BaseTemplate
from template.chat.common.chat_serialize import *
from service.core.logger import Logger
from service.service_container import ServiceContainer
from service.cache.cache_service import CacheService
from service.queue.queue_service import QueueService
import json
import uuid
from datetime import datetime

class ChatTemplateImpl(BaseTemplate):
    def __init__(self):
        super().__init__()
    
    async def on_chat_message_send_req(self, client_session, request: ChatMessageSendRequest):
        """LLM 스트리밍을 위한 메시지 전송 처리"""
        response = ChatMessageSendResponse()
        
        try:
            account_db_key = client_session.session.account_db_key
            shard_id = client_session.session.shard_id
            
            # 1. Redis에 즉시 저장 (실시간 응답을 위해)
            cache_key = f"chat:user:{account_db_key}:room:{request.room_id}:messages"
            message_data = {
                "message_id": f"msg_{uuid.uuid4().hex[:16]}",
                "room_id": request.room_id,
                "sender_type": "USER",
                "content": request.content,
                "timestamp": datetime.now().isoformat(),
                "metadata": {
                    "include_portfolio": request.include_portfolio,
                    "analysis_symbols": request.analysis_symbols
                }
            }
            
            # Redis List에 추가 (최근 100개만 유지)
            async with CacheService.get_client() as client:
                await client.lpush(cache_key, json.dumps(message_data))
                await client.ltrim(cache_key, 0, 99)
                await client.expire(cache_key, 86400)  # 24시간 TTL
            
            # 2. 스트리밍을 위한 세션 상태 저장
            stream_key = f"stream:{account_db_key}:{request.room_id}"
            stream_data = {
                "status": "active", 
                "started_at": datetime.now().isoformat(),
                "message_id": message_data["message_id"]
            }
            async with CacheService.get_client() as client:
                await client.set_string(stream_key, json.dumps(stream_data), expire=300)
            
            # 3. QueueService를 통한 비동기 MySQL 저장
            queue_service = QueueService.get_instance()
            await queue_service.send_message(
                queue_name="chat_persistence",
                payload={
                    "type": "save_user_message",
                    "account_db_key": account_db_key,
                    "shard_id": shard_id,
                    "message_data": message_data
                },
                message_type="chat_save",
                priority=2  # 중간 우선순위
            )
            
            response.errorCode = 0
            response.stream_key = stream_key
            response.message_id = message_data["message_id"]
            
            Logger.info(f"Chat message prepared for streaming: {message_data['message_id']}")
            
        except Exception as e:
            Logger.error(f"Chat message send error: {e}")
            response.errorCode = 1000
            
        return response
    
    async def get_recent_messages_hybrid(
        self, 
        account_db_key: int, 
        room_id: str, 
        limit: int = 50
    ) -> list:
        """Redis + MySQL 하이브리드 조회"""
        
        # 1. Redis에서 최근 메시지 확인
        cache_key = f"chat:user:{account_db_key}:room:{room_id}:messages"
        messages = []
        
        try:
            async with CacheService.get_client() as client:
                cached_messages = await client.lrange(cache_key, 0, limit - 1)
                
                for msg_json in cached_messages:
                    messages.append(json.loads(msg_json))
            
            # 2. Redis에 충분한 데이터가 없으면 MySQL에서 추가 로드
            if len(messages) < limit:
                remaining = limit - len(messages)
                db_service = ServiceContainer.get_database_service()
                
                db_messages = await db_service.call_shard_procedure(
                    shard_id=await self._get_user_shard(account_db_key),
                    procedure_name="fp_get_chat_messages",
                    params=(account_db_key, room_id, 1, remaining, None)
                )
                
                # MySQL 데이터를 Redis에 캐싱
                if db_messages:
                    for msg in db_messages:
                        db_message_data = {
                            "message_id": msg.get('message_id'),
                            "sender_type": msg.get('sender_type'),
                            "content": msg.get('content'),
                            "timestamp": str(msg.get('timestamp')),
                            "metadata": json.loads(msg.get('metadata', '{}'))
                        }
                        messages.append(db_message_data)
            
            return messages
            
        except Exception as e:
            Logger.error(f"Error getting recent messages: {e}")
            return []
    
    async def save_streaming_response(
        self,
        account_db_key: int,
        room_id: str,
        ai_response: str,
        metadata: dict
    ):
        """스트리밍 완료 후 AI 응답 저장"""
        
        # 1. Redis에 임시 저장
        cache_key = f"chat:user:{account_db_key}:room:{room_id}:messages"
        ai_message_data = {
            "message_id": f"msg_{uuid.uuid4().hex[:16]}",
            "room_id": room_id,
            "sender_type": "AI",
            "content": ai_response,
            "timestamp": datetime.now().isoformat(),
            "metadata": metadata
        }
        
        async with CacheService.get_client() as client:
            await client.lpush(cache_key, json.dumps(ai_message_data))
        
        # 2. QueueService를 통한 MySQL 영구 저장
        queue_service = QueueService.get_instance()
        await queue_service.send_message(
            queue_name="chat_persistence",
            payload={
                "type": "save_ai_response",
                "account_db_key": account_db_key,
                "shard_id": await self._get_user_shard(account_db_key),
                "message_data": ai_message_data
            },
            message_type="chat_save",
            priority=1  # 높은 우선순위
        )
    
    async def _get_user_shard(self, account_db_key: int) -> int:
        """사용자 샤드 ID 조회"""
        try:
            db_service = ServiceContainer.get_database_service()
            result = await db_service.execute_global_query(
                "SELECT shard_id FROM table_user_shard_mapping WHERE account_db_key = %s",
                (account_db_key,)
            )
            return result[0]['shard_id'] if result else 1
        except Exception as e:
            Logger.error(f"Error getting user shard: {e}")
            return 1
```

#### 2. SSE 스트리밍 엔드포인트 구현
```python
# base_server/application/base_web_server/routers/chat.py

from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import StreamingResponse
from sse_starlette.sse import EventSourceResponse
from template.base.template_context import TemplateContext, TemplateType
from template.base.template_service import TemplateService
from template.chat.common.chat_serialize import *
from service.cache.cache_service import CacheService
from service.core.logger import Logger
import json
import asyncio
from datetime import datetime

router = APIRouter()

# 기존 chat_protocol 설정은 유지
chat_protocol = ChatProtocol()

def setup_chat_protocol_callbacks():
    """Chat protocol 콜백 설정"""
    chat_template = TemplateContext.get_template(TemplateType.CHAT)
    chat_protocol.on_chat_message_send_req_callback = getattr(chat_template, "on_chat_message_send_req", None)
    # ... 기존 콜백들

@router.post("/stream")
async def stream_chat_response(request: ChatMessageSendRequest, req: Request):
    """LLM 응답을 SSE로 스트리밍"""
    
    # 1. 세션 검증 (TemplateService 패턴 따라)
    ip = req.headers.get("X-Forwarded-For", req.client.host).split(", ")[0]
    
    async def generate_stream():
        try:
            # 2. 사용자 메시지 저장 (TemplateService.run_user 패턴)
            save_result = await TemplateService.run_user(
                req.method,
                "/api/chat/message/send",  # 내부적으로 기존 메시지 저장 로직 사용
                ip,
                request.model_dump_json(),
                chat_protocol.chat_message_send_req_controller
            )
            
            result_data = json.loads(save_result)
            if result_data.get('errorCode', 1000) != 0:
                yield {
                    "event": "error",
                    "data": json.dumps({"error": "Failed to save message"})
                }
                return
            
            # 3. 스트림 상태 관리
            stream_key = result_data.get('stream_key')
            message_id = result_data.get('message_id')
            
            # 스트리밍 시작 알림
            yield {
                "event": "start",
                "data": json.dumps({
                    "message_id": message_id,
                    "timestamp": datetime.now().isoformat()
                })
            }
            
            # 4. LLM 스트리밍 응답 시뮬레이션 (실제로는 외부 LLM API 호출)
            full_response = ""
            sample_response = "안녕하세요! 투자 관련 질문에 대해 도움을 드리겠습니다. 어떤 종목에 관심이 있으신가요?"
            
            # 청크 단위로 전송
            for i, char in enumerate(sample_response):
                # 중단 요청 확인
                async with CacheService.get_client() as client:
                    stop_check = await client.get_string(f"{stream_key}:stop")
                    if stop_check:
                        yield {
                            "event": "stopped",
                            "data": json.dumps({"reason": "User requested stop"})
                        }
                        return
                
                full_response += char
                
                # 3-5자씩 묶어서 전송
                if (i + 1) % 3 == 0 or i == len(sample_response) - 1:
                    yield {
                        "event": "message",
                        "data": json.dumps({
                            "type": "content",
                            "content": char,
                            "delta": char
                        })
                    }
                    await asyncio.sleep(0.05)  # 자연스러운 타이핑 효과
            
            # 5. 분석 결과가 있는 경우
            if request.analysis_symbols:
                analysis_results = {
                    "symbols": request.analysis_symbols,
                    "sentiment": "POSITIVE",
                    "recommendations": [
                        {
                            "symbol": symbol,
                            "action": "BUY",
                            "confidence": 0.75
                        } for symbol in request.analysis_symbols
                    ]
                }
                
                yield {
                    "event": "analysis",
                    "data": json.dumps(analysis_results)
                }
            
            # 6. AI 응답 저장
            chat_template = TemplateContext.get_template(TemplateType.CHAT)
            await chat_template.save_streaming_response(
                account_db_key=1,  # 실제로는 세션에서 가져옴
                room_id=request.room_id,
                ai_response=full_response,
                metadata={"analysis_symbols": request.analysis_symbols}
            )
            
            # 완료 시그널
            yield {
                "event": "done",
                "data": json.dumps({
                    "message_length": len(full_response),
                    "timestamp": datetime.now().isoformat()
                })
            }
            
        except Exception as e:
            Logger.error(f"Stream error: {e}")
            yield {
                "event": "error",
                "data": json.dumps({"error": str(e)})
            }
        finally:
            # 스트림 상태 정리
            if 'stream_key' in locals():
                async with CacheService.get_client() as client:
                    await client.delete(stream_key)
                    await client.delete(f"{stream_key}:stop")
    
    # SSE 응답 반환
    return EventSourceResponse(
        generate_stream(),
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",  # Nginx 버퍼링 비활성화
        }
    )

@router.post("/stream/{room_id}/stop")
async def stop_stream(room_id: str, req: Request):
    """진행 중인 스트림 중단"""
    ip = req.headers.get("X-Forwarded-For", req.client.host).split(", ")[0]
    
    # 임시로 account_db_key=1 사용 (실제로는 세션에서 가져옴)
    stream_key = f"stream:1:{room_id}"
    
    async with CacheService.get_client() as client:
        await client.set_string(f"{stream_key}:stop", "true", expire=10)
    
    return {"status": "stop_requested"}

# 기존 엔드포인트들은 그대로 유지
@router.post("/rooms")
async def chat_room_list(request: ChatRoomListRequest, req: Request):
    """채팅방 목록 조회"""
    ip = req.headers.get("X-Forwarded-For", req.client.host).split(", ")[0]
    return await TemplateService.run_user(
        req.method, req.url.path, ip,
        request.model_dump_json(),
        chat_protocol.chat_room_list_req_controller
    )

# ... 기존 엔드포인트들 계속
```

#### 3. 백그라운드 큐 처리기 (QueueService 활용)
```python
# base_server/service/queue/chat_persistence_worker.py

from service.queue.queue_service import QueueService
from service.queue.message_queue import QueueMessage
from service.service_container import ServiceContainer
from service.core.logger import Logger
import json
import asyncio

class ChatPersistenceWorker:
    """채팅 메시지를 MySQL에 영구 저장하는 워커"""
    
    def __init__(self):
        self.queue_service = QueueService.get_instance()
        self.db_service = ServiceContainer.get_database_service()
        self.running = False
        
    async def start(self):
        """큐 워커 시작"""
        self.running = True
        
        # QueueService의 메시지 소비자로 등록
        await self.queue_service.register_message_consumer(
            queue_name="chat_persistence",
            consumer_id="chat_persistence_worker",
            callback=self._process_message
        )
        
        Logger.info("ChatPersistenceWorker started")
    
    async def stop(self):
        """큐 워커 중지"""
        self.running = False
        Logger.info("ChatPersistenceWorker stopped")
    
    async def _process_message(self, message: QueueMessage) -> bool:
        """메시지 처리"""
        try:
            msg_type = message.payload.get("type")
            
            if msg_type == "save_user_message":
                return await self._save_user_message(message.payload)
            elif msg_type == "save_ai_response":
                return await self._save_ai_response(message.payload)
            else:
                Logger.warn(f"Unknown message type: {msg_type}")
                return False
                
        except Exception as e:
            Logger.error(f"Message processing error: {e}")
            return False
    
    async def _save_user_message(self, payload: dict) -> bool:
        """사용자 메시지 MySQL 저장"""
        try:
            data = payload["message_data"]
            shard_id = payload["shard_id"]
            
            # 기존 프로시저 사용
            result = await self.db_service.call_shard_procedure(
                shard_id,
                "fp_save_chat_message_direct",
                (
                    data["message_id"],
                    data["room_id"],
                    data["sender_type"],
                    data["content"],
                    json.dumps(data.get("metadata", {}))
                )
            )
            
            Logger.info(f"User message saved to MySQL: {data['message_id']}")
            return True
            
        except Exception as e:
            Logger.error(f"Failed to save user message: {e}")
            return False
    
    async def _save_ai_response(self, payload: dict) -> bool:
        """AI 응답 MySQL 저장"""
        try:
            data = payload["message_data"]
            shard_id = payload["shard_id"]
            
            result = await self.db_service.call_shard_procedure(
                shard_id,
                "fp_save_chat_message_direct",
                (
                    data["message_id"],
                    data["room_id"],
                    data["sender_type"],
                    data["content"],
                    json.dumps(data.get("metadata", {}))
                )
            )
            
            Logger.info(f"AI response saved to MySQL: {data['message_id']}")
            return True
            
        except Exception as e:
            Logger.error(f"Failed to save AI response: {e}")
            return False

# main.py에서 워커 시작
async def start_chat_persistence_worker():
    """채팅 영속성 워커 시작"""
    if QueueService._initialized:
        worker = ChatPersistenceWorker()
        await worker.start()
        return worker
    return None
```

---

## 2. LLM 응답 스트리밍 구현 방식 결정

### 🤔 의사결정 과정

#### 고민했던 선택지들

| 선택지 | 장점 | 단점 | 판단 |
|--------|------|------|------|
| **SSE** | • HTTP 기반 (인프라 호환)<br>• 자동 재연결<br>• 구현 단순 | • 단방향 통신만 가능<br>• 텍스트만 전송 | ✅ LLM 스트리밍에 최적 |
| **WebSocket** | • 양방향 실시간 통신<br>• 바이너리 지원 | • 프록시 설정 복잡<br>• Sticky session 필요 | ❌ 현재 요구사항에 과도함 |

#### 🎯 최종 선택: SSE (Server-Sent Events)

**선택 이유:**
1. LLM 스트리밍은 본질적으로 단방향 통신
2. 브라우저가 자동으로 재연결 처리
3. 모든 HTTP 인프라와 완벽 호환
4. FastAPI에서 EventSourceResponse 네이티브 지원

### 💻 프론트엔드 통합 코드

#### React Hook 구현 (base_server 프론트엔드와 통합)
```typescript
// base_server/frontend/ai-trading-platform/hooks/use-chat-stream.ts

import { useCallback, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from '@/lib/store/hooks';
import { addMessage, updateStreamingMessage } from '@/lib/store/slices/chat-slice';

interface StreamOptions {
  roomId: string;
  content: string;
  includePortfolio?: boolean;
  analysisSymbols?: string[];
}

export function useChatStream() {
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((state) => state.auth);
  const [isStreaming, setIsStreaming] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);
  const currentMessageRef = useRef<string>('');

  const startStream = useCallback(async (options: StreamOptions) => {
    if (isStreaming) return;
    
    setIsStreaming(true);
    currentMessageRef.current = '';

    try {
      // 1. SSE 연결 시작 (base_server API 엔드포인트 사용)
      const params = new URLSearchParams({
        room_id: options.roomId,
        content: options.content,
        include_portfolio: String(options.includePortfolio || false),
        analysis_symbols: JSON.stringify(options.analysisSymbols || [])
      });

      const eventSource = new EventSource(
        `/api/chat/stream?${params}`,
        { withCredentials: true }
      );

      // 2. 이벤트 핸들러 설정
      eventSource.addEventListener('start', (event) => {
        const data = JSON.parse(event.data);
        dispatch(addMessage({
          id: data.message_id,
          roomId: options.roomId,
          type: 'ai',
          content: '',
          timestamp: data.timestamp,
          isStreaming: true
        }));
      });

      eventSource.addEventListener('message', (event) => {
        const data = JSON.parse(event.data);
        if (data.type === 'content') {
          currentMessageRef.current += data.content;
          dispatch(updateStreamingMessage({
            roomId: options.roomId,
            content: currentMessageRef.current
          }));
        }
      });

      eventSource.addEventListener('analysis', (event) => {
        const analysisData = JSON.parse(event.data);
        // 분석 결과를 포트폴리오 슬라이스에 업데이트
        console.log('Analysis results:', analysisData);
      });

      eventSource.addEventListener('done', (event) => {
        dispatch(updateStreamingMessage({
          roomId: options.roomId,
          content: currentMessageRef.current,
          isStreaming: false
        }));
        eventSource.close();
        setIsStreaming(false);
      });

      eventSource.addEventListener('error', (event) => {
        console.error('SSE Error:', event);
        eventSource.close();
        setIsStreaming(false);
      });

      eventSourceRef.current = eventSource;

    } catch (error) {
      console.error('Stream error:', error);
      setIsStreaming(false);
    }
  }, [dispatch, isStreaming]);

  const stopStream = useCallback(async (roomId: string) => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }

    // 서버에 중단 요청
    await fetch(`/api/chat/stream/${roomId}/stop`, {
      method: 'POST',
      credentials: 'include'
    });

    setIsStreaming(false);
  }, []);

  return { startStream, stopStream, isStreaming };
}
```

### 🚀 운영 환경 설정

#### Nginx 설정 (base_server 배포용)
```nginx
# /etc/nginx/sites-available/base_server

upstream base_server_backend {
    server 127.0.0.1:8000;
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
}

server {
    listen 443 ssl http2;
    server_name api.base-server.com;

    # SSE 엔드포인트 설정
    location /api/chat/stream {
        proxy_pass http://base_server_backend;
        
        # SSE 필수 설정
        proxy_set_header Connection '';
        proxy_http_version 1.1;
        chunked_transfer_encoding off;
        proxy_buffering off;
        proxy_cache off;
        
        # 타임아웃 설정 (LLM 응답 시간 고려)
        proxy_read_timeout 300s;
        keepalive_timeout 300s;
        
        # 헤더 설정
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 일반 API 엔드포인트
    location /api {
        proxy_pass http://base_server_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

---

## 3. base_server 아키텍처 통합 인사이트

### 📊 의사결정 매트릭스

| 기준 | 가중치 | Redis+MySQL | Redis+ES | SSE | WebSocket |
|------|--------|-------------|----------|-----|-----------|
| 기존 인프라 활용 | 30% | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |
| 구현 복잡도 | 25% | ⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ |
| 운영 안정성 | 25% | ⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ |
| 비용 효율성 | 20% | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

### 🎯 핵심 인사이트

```
"최고의 기술" ≠ "최적의 기술"
```

#### base_server의 강점 활용
1. **ServiceContainer 패턴**: 모든 서비스가 중앙 집중식으로 관리
2. **TemplateService 패턴**: 인증/세션 관리가 이미 구현됨
3. **QueueService**: 메시지큐/이벤트큐 인프라 준비됨
4. **Protocol 기반 통신**: 타입 안전한 API 통신 구조

#### 점진적 확장 전략
```
Phase 1: SSE + Redis/MySQL (✅ 현재)
         ↓
Phase 2: + OpenSearch (향후 검색 강화)
         ↓  
Phase 3: + WebSocket (실시간 협업 시)
```

### 💡 배운 점

1. **기존 아키텍처 존중**
   - base_server의 Template-Service-Protocol 패턴 활용
   - 새로운 패러다임보다 기존 구조에 맞는 확장

2. **실용주의적 접근**
   - 지금 당장 필요한 것에 집중
   - 과도한 미래 준비보다 점진적 개선

3. **팀 역량 고려**
   - 이미 숙련된 패턴과 도구 활용
   - 새로운 기술 학습보다 기존 역량 극대화

---

## 4. 구현 계획

### Phase 1: 기본 스트리밍 구현
- [ ] ChatTemplateImpl에 스트리밍 메서드 추가
- [ ] chat 라우터에 SSE 엔드포인트 구현
- [ ] ChatPersistenceWorker 구현 및 등록

### Phase 2: 프론트엔드 통합  
- [ ] useChatStream 훅 구현
- [ ] chat-slice에 스트리밍 상태 추가
- [ ] 채팅 UI 컴포넌트 스트리밍 대응

### Phase 3: 운영 환경 준비
- [ ] Nginx 설정 업데이트  
- [ ] 모니터링 및 로깅 설정
- [ ] 성능 테스트 및 최적화

---

이번 주차를 통해 **"왜 이 기술을 선택했는가?"**라는 질문에 명확히 답할 수 있는 의사결정 역량과 함께, **기존 아키텍처를 존중하면서도 현대적 기능을 추가하는 방법**을 학습할 수 있었습니다. 실무에서는 최신 기술보다 **팀과 프로젝트에 적합한 기술 선택**이 성공의 핵심임을 다시 한번 깨달았습니다.