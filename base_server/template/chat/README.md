# 📁 Chat Template

## 📌 개요
Chat Template은 AI 기반 챗봇 시스템의 핵심 비즈니스 로직을 담당하는 템플릿입니다. Redis + MySQL 하이브리드 아키텍처를 통해 실시간 채팅과 영속성 저장을 동시에 제공하며, State Machine 기반의 원자적 상태 관리로 Race Condition을 해결합니다. AIChatService와 연동하여 LLM 기반의 지능형 대화를 지원합니다.

## 🏗️ 구조
```
base_server/template/chat/
├── chat_template_impl.py          # 채팅 템플릿 구현체 (Redis + MySQL 하이브리드)
├── chat_state_machine.py          # 채팅 상태 머신 (Redis 기반 원자적 상태 관리)
├── chat_persistence_consumer.py   # 채팅 메시지 DB 저장 컨슈머 (MessageQueue → Scheduler → DB)
├── common/                        # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── chat_model.py             # 채팅 데이터 모델 (ChatRoom, ChatMessage)
│   ├── chat_protocol.py          # 채팅 프로토콜 정의
│   └── chat_serialize.py         # 채팅 직렬화 클래스 (요청/응답 모델)
└── README.md                      
```

## 🔧 핵심 기능

### **ChatTemplateImpl 클래스**
- **채팅방 목록 조회**: `on_chat_room_list_req()` - Redis + MySQL 하이브리드 조회, State Machine 기반 DELETING/DELETED 상태 필터링
- **채팅방 생성**: `on_chat_room_create_req()` - UUID 기반 방 ID 생성, State Machine CREATING → PENDING 전이, MessageQueue 기반 비동기 DB 저장
- **메시지 전송**: `on_chat_message_send_req()` - AIChatService.chat() 호출, 사용자/AI 메시지 각각 State Machine 관리, Redis 실시간 캐싱 + MessageQueue 비동기 DB 저장
- **메시지 목록 조회**: `on_chat_message_list_req()` - Redis 우선 조회, DB fallback, 페이징 지원, AI 히스토리 자동 로드
- **채팅방 삭제**: `on_chat_room_delete_req()` - State Machine ACTIVE → DELETING 전이, Redis 즉시 삭제, MessageQueue 기반 DB Soft Delete
- **채팅방 제목 변경**: `on_chat_room_update_req()` - Redis 캐시 즉시 업데이트, MessageQueue 기반 DB 업데이트
- **메시지 삭제**: `on_chat_message_delete_req()` - State Machine 지능형 삭제, Redis 캐시 무효화, MessageQueue 기반 DB 삭제

### **ChatStateMachine 클래스**
- **메시지 상태 관리**: COMPOSING → PENDING → PROCESSING → SENT → DELETING → DELETED
- **방 상태 관리**: CREATING → PENDING → PROCESSING → ACTIVE → DELETING → DELETED
- **원자적 상태 전이**: Redis Lua Script로 Race Condition 방지, 전이 규칙 검증
- **지능형 삭제**: smart_delete_message() 메서드로 메시지 삭제 상태 관리
- **분산 환경 지원**: CacheService와 동일한 정적 클래스 싱글톤 패턴, get_chat_state_machine() 함수

### **ChatPersistenceConsumer 클래스**
- **비동기 DB 저장**: MessageQueue → Scheduler → DB 아키텍처, LockService 기반 순서 보장
- **배치 처리**: 50개 메시지 단위, 3초 간격 배치 저장, 30초마다 버퍼 정리
- **샤드 라우팅**: session.shard_id 기반 정확한 샤드 DB 접근, 매핑 테이블 활용
- **멀티 프로세스 지원**: 고유한 컨슈머 ID와 작업 ID 생성, 프로세스별 독립적 스케줄러 등록
- **메시지 타입별 처리**: CHAT_ROOM_CREATE, CHAT_MESSAGE_SAVE, CHAT_ROOM_DELETE, CHAT_ROOM_UPDATE, CHAT_MESSAGE_DELETE

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **AIChatService**: LLM 기반 AI 채팅 처리 (ServiceContainer.get_ai_chat_service()), chat() 메서드 호출, mem() 세션 관리
- **CacheService**: Redis 기반 실시간 데이터 저장 및 캐싱 (get_client(), set_string, list_push_right, set_expire)
- **QueueService**: 메시지 큐를 통한 비동기 DB 저장 작업 (get_queue_service(), send_message, QueueMessage)
- **DatabaseService**: 샤드 DB 연동 및 저장 프로시저 호출 (call_shard_procedure)
- **SchedulerService**: 배치 처리 및 버퍼 정리 스케줄링 (add_job, ScheduleJob)

### **연동 방식 설명**
1. **AI 채팅 처리** → AIChatService.chat() 메서드 호출, mem(session_id).chat_memory로 대화 히스토리 관리
2. **실시간 데이터 관리** → CacheService.get_client()로 Redis 클라이언트 획득, set_string/list_push_right로 즉시 저장
3. **영속성 보장** → QueueService.get_instance()로 큐 서비스 획득, QueueMessage로 구조화된 메시지 전송
4. **상태 관리** → get_chat_state_machine()으로 상태 머신 인스턴스 획득, transition_room/transition_message로 상태 전이
5. **샤드 라우팅** → client_session.session.shard_id 기반 정확한 샤드 DB 접근, 매핑 테이블 활용
6. **메시지 큐 처리** → chat_persistence 큐에 메시지 타입별 페이로드 전송, partition_key로 채팅방별 순서 보장

## 📊 데이터 흐름

### **Request → Template → Service → Response**

```
1. 채팅 요청 (Request)
   ↓
2. ChatTemplateImpl.on_*_req() 메서드 호출
   ↓
3. Redis 우선 조회/저장 (실시간성 확보)
   ↓
4. State Machine 상태 관리 (Race Condition 방지)
   ↓
5. Queue 기반 비동기 DB 저장 (영속성 보장)
   ↓
6. 채팅 응답 (Response)
```

### **채팅방 목록 조회 플로우**
```
1. 채팅방 목록 요청
   ↓
2. Redis에서 rooms:{account_id} 키로 세션 목록 조회
   ↓
3. State Machine으로 각 방의 상태 확인 (DELETING/DELETED 필터링)
   ↓
4. Redis 캐시 미스 시 DB에서 fp_chat_rooms_get 프로시저 호출
   ↓
5. DB 데이터를 Redis에 캐싱 (1시간 TTL)
   ↓
6. ChatRoomListResponse 반환
```

### **메시지 전송 플로우**
```
1. 메시지 전송 요청
   ↓
2. UUID 기반 message_id 생성
   ↓
3. Redis에 즉시 저장 (실시간 응답을 위해)
   ↓
4. State Machine으로 메시지 상태를 PENDING으로 설정
   ↓
5. QueueService를 통한 비동기 DB 저장 작업 전송
   ↓
6. AIChatService를 통한 LLM 응답 생성
   ↓
7. ChatMessageSendResponse 반환
```

### **메시지 영속성 저장 플로우**
```
1. MessageQueue에서 채팅 메시지 이벤트 수신
   ↓
2. ChatPersistenceConsumer의 메시지 버퍼에 누적
   ↓
3. SchedulerService를 통한 3초마다 배치 처리
   ↓
4. LockService를 통한 DB 저장 순서 보장
   ↓
5. fp_chat_message_save 프로시저로 샤드 DB에 저장
   ↓
6. State Machine으로 메시지 상태를 SENT로 전이
```

### **상태 전이 플로우**
```
1. 상태 변경 요청
   ↓
2. Redis Lua Script로 원자적 상태 전이 검증
   ↓
3. 현재 상태와 전이 가능한 상태 목록 비교
   ↓
4. 유효한 전이인 경우 새 상태로 업데이트
   ↓
5. 전이 로그 기록 및 TTL 설정
   ↓
6. 상태 변경 완료 응답
```

## 🚀 사용 예제

### **채팅방 목록 조회 예제**
```python
# 채팅방 목록 조회 요청 처리
async def on_chat_room_list_req(self, client_session, request):
    """채팅방 목록 조회 (Redis + MySQL 하이브리드)"""
    response = ChatRoomListResponse()
    try:
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        shard_id = getattr(client_session.session, 'shard_id', 1)
        user_key = f"rooms:{client_session.session.account_id}"
        rooms = []
        
        # 1단계: Redis에서 챗봇 세션 목록 조회 시도
        redis_success = False
        try:
            async with CacheService.get_client() as redis:
                room_ids = await redis._client.smembers(redis._get_key(user_key))
                if room_ids:  # Redis에 데이터가 있으면
                    state_machine = get_chat_state_machine()
                    for room_id in room_ids:
                        # State Machine으로 방 상태 확인
                        room_state = await state_machine.get_room_state(room_id)
                        
                        # 삭제 중이거나 삭제된 방은 목록에서 제외
                        if room_state in [RoomState.DELETING, RoomState.DELETED]:
                            continue
                        
                        room_key = f"room:{room_id}"
                        raw = await redis.get_string(room_key)
                        if raw:
                            room_data = json.loads(raw)
                            rooms.append(ChatRoom(**room_data))
                    redis_success = True
        except Exception as redis_e:
            Logger.warn(f"Redis 챗봇 세션 목록 조회 실패: {redis_e}")
        
        # 2단계: Redis 실패 또는 비어있을 때 DB에서 조회
        if not redis_success or not rooms:
            database_service = ServiceContainer.get_database_service()
            db_result = await database_service.call_shard_procedure(
                shard_id, 'fp_chat_rooms_get', (account_db_key,)
            )
            
            if db_result:
                for row in db_result:
                    room_data = {
                        "room_id": str(row.get('room_id', '')),
                        "title": str(row.get('title', '')),
                        "ai_persona": str(row.get('ai_persona', '')),
                        "created_at": row.get('created_at').isoformat() if row.get('created_at') else '',
                        "last_message_at": row.get('last_message_at').isoformat() if row.get('last_message_at') else '',
                        "message_count": str(row.get('message_count', 0))
                    }
                    rooms.append(ChatRoom(**room_data))
        
        response.rooms = rooms
        response.total_count = len(rooms)
        response.errorCode = 0
        
    except Exception as e:
        Logger.error(f"Chatbot session list error: {e}")
        response.errorCode = 1000
        response.rooms = []
        response.total_count = 0
    
    return response
```

### **메시지 전송 예제**
```python
# 메시지 전송 요청 처리
async def on_chat_message_send_req(self, client_session, request):
    """LLM 스트리밍을 위한 메시지 전송 처리"""
    response = ChatMessageSendResponse()
    try:
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        shard_id = getattr(client_session.session, 'shard_id', 1)
        
        # 1. 메시지 ID 생성 및 데이터 준비
        message_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        
        message_data = {
            "message_id": message_id,
            "room_id": request.room_id,
            "sender_type": "USER",
            "content": request.content,
            "timestamp": now,
            "metadata": {"ai_persona": request.ai_persona}
        }
        
        # 2. Redis에 즉시 저장 (실시간 응답을 위해)
        msg_key = f"messages:{request.room_id}"
        async with CacheService.get_client() as redis:
            await redis.list_push_right(msg_key, json.dumps(message_data))
            await redis.set_expire(msg_key, 3600)  # 1시간 TTL
        
        # 3. State Machine으로 메시지 상태를 PENDING으로 설정
        state_machine = get_chat_state_machine()
        await state_machine.transition_message(message_id, MessageState.PENDING)
        
        # 4. QueueService를 통한 비동기 MySQL 저장
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
            priority=2
        )
        
        # 5. AIChatService를 통한 LLM 응답 생성
        ai_response = await self.ai_service.process_message(
            room_id=request.room_id,
            user_message=request.content,
            ai_persona=request.ai_persona
        )
        
        response.errorCode = 0
        response.message = ChatMessage(**message_data)
        
        Logger.info(f"Chat message sent: {message_id}")
        
    except Exception as e:
        Logger.error(f"Chat message send error: {e}")
        response.errorCode = 1001
    
    return response
```

### **상태 머신 사용 예제**
```python
# 채팅 상태 머신 사용 예제
async def manage_chat_state():
    """채팅 상태 관리 예제"""
    state_machine = get_chat_state_machine()
    
    # 방 생성 상태 전이
    room_id = "room_123"
    await state_machine.transition_room(room_id, RoomState.CREATING)
    await state_machine.transition_room(room_id, RoomState.PENDING)
    await state_machine.transition_room(room_id, RoomState.PROCESSING)
    await state_machine.transition_room(room_id, RoomState.ACTIVE)
    
    # 메시지 상태 전이
    message_id = "msg_456"
    await state_machine.transition_message(message_id, MessageState.PENDING)
    await state_machine.transition_message(message_id, MessageState.PROCESSING)
    await state_machine.transition_message(message_id, MessageState.SENT)
    
    # 상태 조회
    room_state = await state_machine.get_room_state(room_id)
    message_state = await state_machine.get_message_state(message_id)
    
    Logger.info(f"Room {room_id} state: {room_state.value}")
    Logger.info(f"Message {message_id} state: {message_state.value}")
```

## ⚙️ 설정

### **Redis 캐싱 설정**
- **채팅방 목록 TTL**: 3600초 (1시간)
- **메시지 목록 TTL**: 3600초 (1시간)
- **스트리밍 세션 TTL**: 300초 (5분)
- **상태 머신 TTL**: 86400초 (24시간)

### **배치 처리 설정**
- **배치 크기**: 50개 메시지
- **배치 간격**: 3초
- **버퍼 정리 간격**: 30초
- **Lock 타임아웃**: 10초
- **Lock TTL**: 30초

### **샤드 라우팅 설정**
- **샤드 ID 획득**: client_session.session.shard_id
- **기본 샤드**: 1 (shard_id가 없을 때)
- **샤드 매핑**: 매핑 테이블 기반 정확한 샤드 DB 접근

### **State Machine 설정**
- **메시지 상태**: COMPOSING → PENDING → PROCESSING → SENT → DELETING → DELETED
- **방 상태**: CREATING → PENDING → PROCESSING → ACTIVE → DELETING → DELETED
- **상태 전이 검증**: Redis Lua Script로 원자적 전이 보장
- **전이 로그 TTL**: 86400초 (24시간)

### **AI 채팅 설정**
- **AI 서비스**: ServiceContainer.get_ai_chat_service()로 AIChatService 획득
- **페르소나 지원**: GPT4O 등 다양한 AI 페르소나 설정 가능
- **스트리밍 지원**: 실시간 LLM 응답 스트리밍

## 🔗 연관 폴더

### **의존성 관계**
- **`service.llm.AIChat_service`**: AIChatService - LLM 기반 AI 채팅 처리
- **`service.cache.cache_service`**: CacheService - Redis 기반 실시간 데이터 관리
- **`service.queue.queue_service`**: QueueService - 메시지 큐 기반 비동기 처리
- **`service.db.database_service`**: DatabaseService - 샤드 DB 연동
- **`service.scheduler.scheduler_service`**: SchedulerService - 배치 처리 스케줄링

### **데이터 흐름 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스
- **`service.queue.message_queue`**: QueueMessage, MessagePriority - 메시지 큐 구조
- **`service.scheduler.base_scheduler`**: ScheduleJob, ScheduleType - 스케줄러 작업 정의

### **기본 템플릿 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스 상속
- **`template.base.client_session`**: ClientSession - 클라이언트 세션 관리

### **외부 서비스 연동**
- **`service.llm.AIChat_service`**: AIChatService - LLM 모델 연동
- **`service.cache.cache_service`**: CacheService - Redis 캐시 연동
- **`service.queue.queue_service`**: QueueService - 메시지 큐 연동

---
