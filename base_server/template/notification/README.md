# 📁 Notification Template

## 📌 개요
Notification Template은 인앱 알림, 이메일, SMS, Push 알림 등 멀티채널 알림 시스템을 담당하는 템플릿입니다. Redis 메시지 큐 기반의 비동기 처리, 샤드 DB를 통한 알림 데이터 관리, 그리고 게임 패턴의 자동 삭제 기능을 제공합니다. 운영자용 알림 생성 및 사용자별 알림 설정 관리도 지원합니다.

## 🏗️ 구조
```
base_server/template/notification/
├── notification_template_impl.py          # 알림 템플릿 구현체
├── notification_persistence_consumer.py   # 알림 메시지 DB 저장 및 멀티채널 발송 컨슈머
├── common/                               # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── notification_model.py             # 알림 데이터 모델
│   ├── notification_protocol.py          # 알림 프로토콜 정의
│   └── notification_serialize.py         # 알림 직렬화 클래스
└── README.md                             
```

## 🔧 핵심 기능

### **NotificationTemplateImpl 클래스**
- **알림 목록 조회**: `on_notification_list_req()` - 읽음 상태별 필터링 및 읽은 알림 자동 삭제
- **알림 읽음 처리**: `on_notification_mark_read_req()` - 개별 알림 읽음 처리
- **일괄 읽음 처리**: `on_notification_mark_all_read_req()` - 타입별 일괄 읽음 처리
- **알림 삭제**: `on_notification_delete_req()` - 소프트 삭제 방식
- **알림 통계 조회**: `on_notification_stats_req()` - 일별 통계 및 우선순위별 카운트
- **운영자 알림 생성**: `on_notification_create_req()` - 전체/특정 사용자/사용자 그룹 대상 알림 생성

### **NotificationPersistenceConsumer 클래스**
- **배치 처리**: `_process_batch()` - 모든 샤드의 배치 처리
- **샤드별 처리**: `_process_shard_batch()` - 특정 샤드의 배치 처리
- **채널별 발송**: 인앱(DB 저장), 이메일, SMS, WebSocket, Push 알림 처리
- **분산 락**: LockService를 통한 DB 저장 순서 보장
- **메모리 최적화**: `_cleanup_empty_buffers()` - 빈 버퍼 정리

### **주요 메서드**
- `on_notification_list_req()`: 읽음 상태별 필터링, 읽은 알림 자동 삭제, 페이징 처리
- `on_notification_mark_read_req()`: 개별 알림 읽음 처리 및 상태 업데이트
- `on_notification_mark_all_read_req()`: 타입별 일괄 읽음 처리 및 카운트 반환
- `on_notification_delete_req()`: 소프트 삭제 방식으로 알림 비활성화
- `on_notification_stats_req()`: 일별 통계, 우선순위별 카운트, 실시간 미읽음 수
- `on_notification_create_req()`: 운영자 권한 기반 대량 알림 생성
- `_process_batch()`: 모든 샤드의 배치 처리 및 샤드별 분산 처리
- `_process_shard_batch()`: 특정 샤드의 배치 처리 및 채널별 그룹화
- `_cleanup_empty_buffers()`: 빈 버퍼 정리 및 메모리 최적화

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **DatabaseService**: 샤드 DB 연동 및 저장 프로시저 호출
- **SchedulerService**: 배치 처리 및 버퍼 정리 스케줄링
- **LockService**: DB 저장 순서 보장 및 중복 처리 방지
- **QueueService**: Redis 메시지 큐 처리 및 이벤트 수신
- **EmailService**: 이메일 알림 발송
- **SMSService**: SMS 알림 발송
- **WebSocketService**: 실시간 인앱 알림 전송

### **연동 방식 설명**
1. **알림 생성** → DatabaseService를 통한 DB 저장 및 멀티채널 발송
2. **메시지 큐** → QueueService를 통한 Redis 기반 비동기 처리
3. **데이터 저장** → DatabaseService를 통한 샤드 DB 저장
4. **배치 처리** → SchedulerService를 통한 정기적인 배치 작업
5. **순서 보장** → LockService를 통한 DB 저장 순서 보장
6. **상태 관리** → 샤드 DB를 통한 사용자별 알림 상태 관리

## 📊 데이터 흐름

### **Request → Template → Service → Response**

```
1. 알림 목록 조회 요청 (Request)
   ↓
2. NotificationTemplateImpl.on_notification_list_req()
   ↓
3. DatabaseService.call_shard_procedure() - 샤드 DB에서 알림 조회
   ↓
4. 읽음 상태별 프로시저 선택 (읽은 알림 자동 삭제 포함)
   ↓
5. 페이징 처리 및 통계 조회
   ↓
6. 알림 목록 응답 (Response)
```

### **메시지 큐 처리 플로우**
```
1. Redis 메시지 큐에서 알림 이벤트 수신
   ↓
2. NotificationPersistenceConsumer._process_batch()
   ↓
3. 샤드별 버퍼에 메시지 누적
   ↓
4. LockService.acquire() - DB 저장 순서 보장
   ↓
5. 배치 단위로 DB 저장 및 멀티채널 발송
   ↓
6. LockService.release() - 락 해제
```

### **운영자 알림 생성 플로우**
```
1. 운영자 권한 확인 (TemplateService.run_operator)
   ↓
2. 대상 사용자 결정 (전체/특정 사용자/사용자 그룹)
   ↓
3. DatabaseService.call_procedure() - fp_operator_notification_create
   ↓
4. 대상별 알림 생성 및 ID 목록 반환
   ↓
5. 생성 결과 및 통계 응답
```

## 🚀 사용 예제

### **알림 목록 조회 예제**
```python
# 알림 목록 조회 요청 처리
async def on_notification_list_req(self, client_session, request: NotificationListRequest):
    """인앱 알림 목록 조회 요청 처리"""
    response = NotificationListResponse()
    response.sequence = request.sequence
    
    try:
        account_db_key = getattr(client_session.session, 'account_db_key', 0)
        shard_id = getattr(client_session.session, 'shard_id', 1)
        
        Logger.info(f"인앱 알림 목록 조회: account={account_db_key}, filter={request.read_filter}, type={request.type_id}")
        
        database_service = ServiceContainer.get_database_service()
        
        # 페이징 처리
        limit = request.limit if request.limit > 0 else 20
        offset = (request.page - 1) * limit if request.page > 0 else 0
        
        # 1. 적절한 프로시저 선택 (읽음 상태에 따라)
        if request.read_filter == "read_only":
            # 읽은 알림만 조회 + 자동 삭제 (게임 패턴)
            procedure_name = "fp_inapp_notifications_get_read_and_delete"
            Logger.info(f"게임 패턴: 읽은 알림 조회 + 자동 삭제")
        elif request.read_filter == "unread_only":
            # 읽지 않은 알림만 조회 (기본값)
            procedure_name = "fp_inapp_notifications_get_unread"
        else:  # "all"
            # 전체 알림 조회 (읽음/안읽음 모두)
            procedure_name = "fp_inapp_notifications_get_all"
        
        # 2. 알림 목록 조회
        db_result = await database_service.call_shard_procedure(
            shard_id,
            procedure_name,
            (account_db_key, request.type_id, limit, offset)
        )
        
        if not db_result:
            response.notifications = []
            response.total_count = 0
            response.unread_count = 0
            response.has_more = False
            response.errorCode = 0
            return response
        
        # 3. 결과 처리 (채팅 패턴과 동일)
        notifications = []
        for row in db_result:
            try:
                data_json = json.loads(row.get('data', '{}')) if row.get('data') else {}
                
                notification = InAppNotification(
                    idx=int(row.get('idx', 0)),
                    notification_id=str(row.get('notification_id', '')),
                    account_db_key=int(row.get('account_db_key', 0)),
                    type_id=str(row.get('type_id', '')),
                    title=str(row.get('title', '')),
                    message=str(row.get('message', '')),
                    data=data_json,
                    priority=int(row.get('priority', 3)),
                    is_read=bool(row.get('is_read', 0)),
                    read_at=row.get('read_at').isoformat() if row.get('read_at') else None,
                    expires_at=row.get('expires_at').isoformat() if row.get('expires_at') else None,
                    created_at=row.get('created_at').isoformat() if row.get('created_at') else '',
                    updated_at=row.get('updated_at').isoformat() if row.get('updated_at') else ''
                )
                
                notifications.append(notification)
                
            except Exception as parse_error:
                Logger.warn(f"알림 파싱 오류 (건너뜀): {parse_error}")
                continue
        
        # 4. 통계 조회 (현재 미읽은 알림 수)
        unread_count = 0
        if request.read_filter != "read_only":  # 읽은 알림 조회가 아닐 때만
            try:
                stats_result = await database_service.call_shard_procedure(
                    shard_id,
                    "fp_inapp_notification_stats_get",
                    (account_db_key, 1)  # 최근 1일
                )
                
                if stats_result:
                    # 마지막 행에서 current_unread_count 찾기
                    for row in stats_result:
                        if 'current_unread_count' in row:
                            unread_count = int(row.get('current_unread_count', 0))
                            break
                            
            except Exception as stats_error:
                Logger.warn(f"통계 조회 실패: {stats_error}")
        
        response.notifications = notifications
        response.total_count = len(notifications)
        response.unread_count = unread_count
        response.has_more = len(notifications) >= limit
        response.errorCode = 0
        
        # 읽은 알림 자동 삭제 시 로그
        if request.read_filter == "read_only" and response.total_count > 0:
            Logger.info(f"게임 패턴: {response.total_count}개 읽은 알림 자동 삭제 완료 (user={account_db_key})")
        
    except Exception as e:
        response.errorCode = 1000
        Logger.error(f"인앱 알림 목록 조회 오류: {e}")
    
    return response
```

### **운영자 알림 생성 예제**
```python
# 운영자 알림 생성 요청 처리
async def on_notification_create_req(self, client_session, request: NotificationCreateRequest):
    """운영자 알림 생성 요청 (운영진용)"""
    response = NotificationCreateResponse()
    response.sequence = request.sequence
    
    try:
        # 운영자 권한 확인은 TemplateService.run_operator에서 이미 처리됨
        operator_account_key = getattr(client_session.session, 'account_db_key', 0)
        
        Logger.info(f"운영자 알림 생성: operator={operator_account_key}, target={request.target_type}, title={request.title}")
        
        database_service = ServiceContainer.get_database_service()
        
        # 대상 사용자 목록 결정
        target_users = []
        if request.target_type == "ALL":
            # 전체 사용자 - 프로시저에서 처리
            target_users = None
        elif request.target_type == "SPECIFIC_USER":
            target_users = request.target_users or []
            if not target_users:
                response.notification_ids = []
                response.created_count = 0
                response.message = "특정 사용자 지정 시 target_users가 필요합니다"
                response.errorCode = 9001
                return response
        elif request.target_type == "USER_GROUP":
            # 사용자 그룹 (PREMIUM, FREE 등) - 프로시저에서 처리
            if not request.user_group:
                response.notification_ids = []
                response.created_count = 0
                response.message = "사용자 그룹 지정 시 user_group이 필요합니다"
                response.errorCode = 9002
                return response
        
        # JSON 데이터 직렬화
        data_json = json.dumps(request.data) if request.data else None
        
        # 알림 생성 프로시저 호출
        db_result = await database_service.call_procedure(
            "fp_operator_notification_create",
            (
                request.target_type,
                json.dumps(target_users) if target_users else None,
                request.user_group,
                request.type_id,
                request.title,
                request.message,
                data_json,
                request.priority,
                request.expires_at,
                operator_account_key  # 생성자 기록용
            )
        )
        
        if not db_result:
            response.notification_ids = []
            response.created_count = 0
            response.message = "알림 생성 실패"
            response.errorCode = 9003
            return response
        
        # 결과 처리
        result_row = db_result[0] if db_result else {}
        db_result_status = result_row.get('result', 'FAILED')
        
        if db_result_status == 'SUCCESS':
            created_count = int(result_row.get('created_count', 0))
            notification_ids_str = result_row.get('notification_ids', '')
            
            # 생성된 알림 ID 목록 파싱
            notification_ids = []
            if notification_ids_str:
                try:
                    notification_ids = json.loads(notification_ids_str)
                except json.JSONDecodeError:
                    # JSON 파싱 실패 시 문자열 분리
                    notification_ids = [id.strip() for id in notification_ids_str.split(',') if id.strip()]
            
            response.notification_ids = notification_ids
            response.created_count = created_count
            response.message = f"{created_count}개 알림이 생성되었습니다"
            response.errorCode = 0
            
            Logger.info(f"운영자 알림 생성 성공: {created_count}개 생성")
            
        else:
            response.notification_ids = []
            response.created_count = 0
            response.message = result_row.get('message', '알림 생성 실패')
            response.errorCode = 9004
        
    except Exception as e:
        response.notification_ids = []
        response.created_count = 0
        response.message = "알림 생성 중 오류 발생"
        response.errorCode = 1000
        Logger.error(f"운영자 알림 생성 오류: {e}")
    
    return response
```

## ⚙️ 설정

### **배치 처리**
- **batch_size**: 50 (컨슈머 내부 기본값)
- **batch_interval**: 3초 (컨슈머 내부 기본값)

### **락 키/TTL**
- **락 키**: `notification_save_shard_{shard_id}`
- **timeout**: 10초
- **TTL**: 30초

### **큐 등록**
- **queue_name**: "notification_persistence"
- **consumer_id**: 프로세스별 고유 ID 생성

### **프로시저 (예시)**
- **조회**: `fp_inapp_notifications_get_unread`, `fp_inapp_notifications_get_all`, `fp_inapp_notifications_get_read_and_delete`
- **읽음**: `fp_inapp_notification_mark_read`
- **일괄읽음**: `fp_inapp_notifications_mark_all_read`
- **삭제**: `fp_inapp_notification_soft_delete`
- **통계**: `fp_inapp_notification_stats_get`
- **생성**: `fp_operator_notification_create`
- **저장**: `fp_notification_save`
- **연락처조회**: `fp_get_user_contact_info`

## 🔗 연관 폴더

### **의존성 관계**
- **`service.service_container`**: ServiceContainer - 서비스 컨테이너 및 DatabaseService 접근
- **`service.core.logger`**: Logger - 로깅 서비스

### **데이터 흐름 연관**
- **`template.profile`**: 프로필 변경 시 알림 설정 업데이트 (`ProfileUpdateNotificationRequest`)
- **`template.admin`**: 사용자 알림 큐 모니터링 (`user_notifications` 큐)
- **`template.base`**: 알림 설정 관리 (`NotificationConfig`) 및 템플릿 타입 정의

### **기본 템플릿 연관**
- **`template.base.base_template`**: BaseTemplate - 기본 템플릿 클래스

---
