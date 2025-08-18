# 📁 Admin Template

## 📌 개요
Admin Template은 시스템 전체의 상태 모니터링, 헬스체크, 성능 메트릭 수집, 그리고 운영 관리 기능을 담당하는 템플릿입니다. 데이터베이스, 캐시, 큐, 스케줄러 등 모든 서비스의 상태를 종합적으로 점검하고, 서버의 런타임 정보와 세션 상태를 모니터링합니다.

## 🏗️ 구조
```
base_server/template/admin/
├── admin_template_impl.py          # 관리자 템플릿 구현체
├── common/                         # 공통 모델 및 프로토콜
│   ├── __init__.py
│   ├── admin_model.py             # 관리자 데이터 모델
│   ├── admin_protocol.py          # 관리자 프로토콜 정의
│   └── admin_serialize.py         # 관리자 직렬화 클래스
└── README.md                       
```

## 🔧 핵심 기능

### **AdminTemplateImpl 클래스**
- **시스템 헬스체크**: `on_health_check_req()` - 데이터베이스, 캐시, 서비스, 모니터링 상태 종합 점검
- **서버 상태 조회**: `on_server_status_req()` - 서버 정보, 업타임, 시스템 메트릭 수집
- **세션 카운트 조회**: `on_session_count_req()` - Redis 기반 활성 세션 수 모니터링
- **큐 통계 조회**: `on_queue_stats_req()` - 메시지 큐 및 이벤트 큐 상태 분석
- **빠른 테스트**: `on_quick_test_req()` - 핵심 서비스 기능 테스트

### **주요 메서드**
- `on_health_check_req()`: check_type에 따른 조건부 서비스 헬스체크 수행 (all/db/cache/services/monitoring)
- `on_server_status_req()`: 서버 정보, 업타임, include_metrics에 따른 시스템 메트릭 수집
- `on_session_count_req()`: Redis 기반 활성 세션 수 모니터링 (session:* 패턴 키 스캔)
- `on_queue_stats_req()`: 큐 서비스 통계 및 특정 큐 상태 조회
- `on_quick_test_req()`: 캐시, 데이터베이스, 큐, 락 서비스 기능 테스트
- `_check_database_health()`: TemplateService.get_database_service()로 DB 연결 상태 및 응답 시간 측정
- `_check_cache_health()`: CacheService.get_redis_client()로 Redis 연결 상태 및 읽기/쓰기 테스트
- `_check_services_health()`: LockService, SchedulerService, QueueService, CacheService 초기화 상태 확인
- `_get_server_metrics()`: psutil을 통한 CPU, 메모리, 디스크, 네트워크 메트릭 및 서비스별 메트릭 수집
- `_get_session_count()`: CacheService.get_redis_client()로 Redis에서 session:* 패턴 키 개수 조회
- `_get_monitoring_status()`: service_monitor.get_health_summary() 및 get_all_service_health() 호출

## 🔄 Template-Service 연동

### **사용하는 Service 목록**
- **DatabaseService**: 데이터베이스 연결 상태 및 성능 테스트 (TemplateService.get_database_service())
- **CacheService**: Redis 연결 상태 및 읽기/쓰기 테스트, 세션 카운트 조회
- **LockService**: 분산 락 서비스 상태 확인 (is_initialized())
- **SchedulerService**: 스케줄러 서비스 상태 및 작업 정보 조회 (is_initialized(), get_all_jobs_status())
- **QueueService**: 메시지 큐 및 이벤트 큐 통계 수집 (_initialized, get_instance(), get_stats())
- **ServiceMonitor**: 런타임 모니터링 시스템 상태 조회 (get_health_summary(), get_all_service_health())

### **연동 방식 설명**
1. **헬스체크** → check_type에 따른 조건부 서비스 상태 확인 및 응답 시간 측정
2. **메트릭 수집** → psutil을 통한 시스템 리소스 모니터링 (ImportError 시 graceful fallback)
3. **세션 모니터링** → CacheService.get_redis_client()로 Redis 기반 활성 세션 수 추적
4. **큐 모니터링** → QueueService.get_instance().get_stats()로 메시지 큐 처리량 및 상태 분석
5. **성능 테스트** → 각 서비스의 초기화 상태 및 메트릭 수집을 통한 실제 동작 테스트

## 📊 데이터 흐름

### **Request → Template → Service → Response**

```
1. 관리자 요청 (Request)
   ↓
2. AdminTemplateImpl.on_*_req() 메서드 호출
   ↓
3. 내부 헬퍼 메서드 호출 (_check_database_health, _check_cache_health 등)
   ↓
4. 각 서비스 상태 확인 및 응답 시간 측정
   ↓
5. 상태별 우선순위 결정 (unhealthy > degraded > healthy)
   ↓
6. 관리자 응답 (Response)
```

### **헬스체크 플로우**
```
1. 헬스체크 요청 (check_type: all/db/cache/services/monitoring)
   ↓
2. 요청 타입별 조건부 서비스 체크
   ↓
3. _check_database_health() - TemplateService.get_database_service()로 DB 연결 테스트
   ↓
4. _check_cache_health() - CacheService.get_redis_client()로 Redis 연결 테스트
   ↓
5. _check_services_health() - LockService, SchedulerService, QueueService, CacheService 초기화 상태 확인
   ↓
6. _get_monitoring_status() - service_monitor.get_health_summary() 및 get_all_service_health() 호출
   ↓
7. 각 서비스 상태를 바탕으로 overall_status 결정 (unhealthy > degraded > healthy)
   ↓
8. HealthCheckResponse 반환
```

### **서버 상태 및 메트릭 수집 플로우**
```
1. 서버 상태 요청 (include_metrics: true/false)
   ↓
2. uptime 계산 (self.start_time 기준)
   ↓
3. include_metrics가 true인 경우 _get_server_metrics() 호출
   ↓
4. psutil import 시도 (실패 시 graceful fallback)
   ↓
5. CPU, 메모리, 디스크, 네트워크 연결 수 수집
   ↓
6. 서비스별 메트릭 수집 (CacheService.get_metrics(), QueueService.get_stats(), SchedulerService.get_all_jobs_status())
   ↓
7. ServerStatusResponse 반환
```

### **세션 카운트 수집 플로우**
```
1. 세션 카운트 요청
   ↓
2. _get_session_count() 호출
   ↓
3. CacheService.is_initialized() 확인 후 CacheService.get_redis_client()로 Redis 클라이언트 획득
   ↓
4. async with cache_client as client로 "session:*" 패턴의 키 스캔
   ↓
5. 활성 세션 수 반환 (실패 시 0 반환)
```

### **큐 통계 수집 플로우**
```
1. 큐 통계 요청 (queue_names: 사용자 지정 또는 기본값)
   ↓
2. hasattr(QueueService, '_initialized') and QueueService._initialized 확인
   ↓
3. QueueService.get_instance()로 queue_service 획득
   ↓
4. queue_service.get_stats() - 서비스 전체 통계
   ↓
5. queue_service.get_event_stats() - 이벤트 큐 통계
   ↓
6. 요청된 큐별 get_queue_stats() 호출 (에러 시 {"error": str(e)} 반환)
   ↓
7. QueueStatsResponse 반환 (QueueService 미초기화 시 error_code 404)
```

### **빠른 테스트 플로우**
```
1. 빠른 테스트 요청 (test_types: 사용자 지정 또는 기본값)
   ↓
2. 테스트 타입별 조건부 실행
   ↓
3. cache: CacheService.is_initialized() 확인 후 Redis read/write 테스트 (admin_quick_test_cache 키 사용)
   ↓
4. database: TemplateService.get_database_service()로 DatabaseService 연결 테스트 (SELECT 1 as test)
   ↓
5. queue: QueueService._initialized 확인 후 get_stats()로 상태 및 통계 확인
   ↓
6. lock: LockService.is_initialized() 확인 후 is_locked("admin_quick_test_lock") 테스트
   ↓
7. 각 테스트 결과 집계 (passed/failed/skipped) 및 QuickTestResponse 반환
```

## 🚀 사용 예제

### **시스템 헬스체크 예제**
```python
# 시스템 헬스체크 요청 처리
async def on_health_check_req(self, client_session: ClientSession, request: HealthCheckRequest) -> HealthCheckResponse:
    """헬스체크 요청 처리"""
    try:
        services = {}
        overall_status = "healthy"
        
        # 데이터베이스 체크
        if request.check_type in ["all", "db"]:
            db_status = await self._check_database_health()
            services["database"] = db_status
            if db_status["status"] != "healthy":
                overall_status = "unhealthy"
        
        # 캐시 체크
        if request.check_type in ["all", "cache"]:
            cache_status = await self._check_cache_health()
            services["cache"] = cache_status
            if cache_status["status"] != "healthy":
                overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
        # 서비스 체크
        if request.check_type in ["all", "services"]:
            service_status = await self._check_services_health()
            services["services"] = service_status
            if service_status["status"] != "healthy":
                overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
        # 런타임 모니터링 정보 추가
        if request.check_type in ["all", "monitoring"]:
            monitoring_status = await self._get_monitoring_status()
            services["monitoring"] = monitoring_status
            if monitoring_status["status"] != "healthy":
                overall_status = "degraded" if overall_status == "healthy" else "unhealthy"
        
        return HealthCheckResponse(
            status=overall_status,
            timestamp=datetime.now().isoformat(),
            services=services,
            error_code=0
        )
        
    except Exception as e:
        Logger.error(f"Health check failed: {e}")
        return HealthCheckResponse(
            status="unhealthy",
            timestamp=datetime.now().isoformat(),
            services={},
            error_code=500,
            error_message=str(e)
        )
```

### **큐 통계 조회 예제**
```python
# 큐 통계 요청 처리
async def on_queue_stats_req(self, client_session: ClientSession, request: QueueStatsRequest) -> QueueStatsResponse:
    """큐 통계 요청 처리"""
    try:
        if hasattr(QueueService, '_initialized') and QueueService._initialized:
            queue_service = QueueService.get_instance()
            
            # 서비스 전체 통계
            service_stats = queue_service.get_stats()
            
            # 이벤트큐 통계
            event_stats = await queue_service.get_event_stats()
            
            # 특정 큐들의 통계 (요청에 큐 이름이 있으면 사용, 없으면 기본값)
            queue_names = request.queue_names or ["user_notifications", "trade_processing", "risk_analysis", "price_alerts"]
            queue_details = {}
            
            for queue_name in queue_names:
                try:
                    stats = await queue_service.get_queue_stats(queue_name)
                    if stats:
                        queue_details[queue_name] = stats
                except Exception as e:
                    queue_details[queue_name] = {"error": str(e)}
            
            return QueueStatsResponse(
                service_stats=service_stats,
                event_stats=event_stats,
                queue_details=queue_details,
                timestamp=datetime.now().isoformat(),
                error_code=0
            )
        else:
            return QueueStatsResponse(
                service_stats={},
                event_stats={},
                queue_details={},
                timestamp=datetime.now().isoformat(),
                error_code=404,
                error_message="QueueService not initialized"
            )
            
    except Exception as e:
        Logger.error(f"Queue stats request failed: {e}")
        return QueueStatsResponse(
            service_stats={},
            event_stats={},
            queue_details={},
            timestamp=datetime.now().isoformat(),
            error_code=500,
            error_message=str(e)
        )
```

### **빠른 테스트 예제**
```python
# 빠른 테스트 요청 처리
async def on_quick_test_req(self, client_session: ClientSession, request: QuickTestRequest) -> QuickTestResponse:
    """빠른 테스트 요청 처리"""
    try:
        # 테스트할 서비스 목록 (요청에 있으면 사용, 없으면 기본값)
        test_types = request.test_types or ["cache", "database", "queue", "lock"]
        results = {}
        summary = {"total": 0, "passed": 0, "failed": 0}
        
        for test_type in test_types:
            summary["total"] += 1
            try:
                if test_type == "cache":
                    if CacheService.is_initialized():
                        cache_client = CacheService.get_redis_client()
                        async with cache_client as client:
                            test_key = "admin_quick_test_cache"
                            await client.set_string(test_key, "test_value", expire=10)
                            value = await client.get_string(test_key)
                            await client.delete(test_key)
                            
                            if value == "test_value":
                                results[test_type] = {"status": "passed", "details": "Cache read/write successful"}
                                summary["passed"] += 1
                            else:
                                results[test_type] = {"status": "failed", "details": "Cache test failed"}
                                summary["failed"] += 1
                    else:
                        results[test_type] = {"status": "skipped", "details": "Cache service not initialized"}
                
                elif test_type == "database":
                    from template.base.template_service import TemplateService
                    db_service = TemplateService.get_database_service()
                    if db_service:
                        test_result = await db_service.execute_global_query("SELECT 1 as test", ())
                        if test_result:
                            results[test_type] = {"status": "passed", "details": "Database connection successful"}
                            summary["passed"] += 1
                        else:
                            results[test_type] = {"status": "failed", "details": "Database test failed"}
                            summary["failed"] += 1
                    else:
                        results[test_type] = {"status": "skipped", "details": "Database service not initialized"}
                
                elif test_type == "queue":
                    if hasattr(QueueService, '_initialized') and QueueService._initialized:
                        queue_service = QueueService.get_instance()
                        stats = queue_service.get_stats()
                        results[test_type] = {"status": "passed", "details": f"Queue service operational, processed: {stats.get('messages_processed', 0)}"}
                        summary["passed"] += 1
                    else:
                        results[test_type] = {"status": "skipped", "details": "Queue service not initialized"}
                
                elif test_type == "lock":
                    if LockService.is_initialized():
                        test_result = await LockService.is_locked("admin_quick_test_lock")
                        results[test_type] = {"status": "passed", "details": "Lock service operational"}
                        summary["passed"] += 1
                    else:
                        results[test_type] = {"status": "skipped", "details": "Lock service not initialized"}
                
                else:
                    results[test_type] = {"status": "unknown", "details": f"Unknown test type: {test_type}"}
                    summary["failed"] += 1
                    
            except Exception as e:
                results[test_type] = {"status": "failed", "details": f"Test error: {str(e)}"}
                summary["failed"] += 1
        
        return QuickTestResponse(
            results=results,
            summary=summary,
            timestamp=datetime.now().isoformat(),
            error_code=0
        )
        
    except Exception as e:
        Logger.error(f"Quick test request failed: {e}")
        return QuickTestResponse(
            results={},
            summary={"total": 0, "passed": 0, "failed": 0},
            timestamp=datetime.now().isoformat(),
            error_code=500,
            error_message=str(e)
        )
```

## ⚙️ 설정

### **헬스체크 설정**
- **check_type**: "all", "db", "cache", "services", "monitoring" (request.check_type 파라미터)
- **기본값**: 없음 (요청에서 반드시 지정해야 함)
- **상태 우선순위**: unhealthy > degraded > healthy
- **데이터베이스 테스트**: "SELECT 1 as test" 쿼리로 연결 상태 및 응답 시간 측정
- **캐시 테스트**: admin_health_check_test 키 사용, 10초 TTL
- **서비스 초기화 확인**: LockService.is_initialized(), SchedulerService.is_initialized(), QueueService._initialized, CacheService.is_initialized()

### **서버 상태 설정**
- **server_name**: "base_web_server" (하드코딩)
- **environment**: "production" (하드코딩)
- **version**: "1.0.0" (하드코딩)
- **include_metrics**: request.include_metrics 파라미터 (기본값 없음, true/false)
- **uptime 계산**: self.start_time 기준으로 초기화 시점부터 경과 시간 계산

### **세션 모니터링 설정**
- **Redis 키 패턴**: "session:*" (scan_keys로 조회)
- **에러 처리**: CacheService 미초기화 또는 Redis 연결 실패 시 0 반환
- **초기화 확인**: CacheService.is_initialized() 확인 후 Redis 클라이언트 획득

### **큐 모니터링 설정**
- **기본 큐 목록**: ["user_notifications", "trade_processing", "risk_analysis", "price_alerts"] (request.queue_names가 없을 때 사용)
- **사용자 지정 큐**: request.queue_names로 특정 큐 지정 가능
- **QueueService 초기화 확인**: hasattr(QueueService, '_initialized') and QueueService._initialized
- **에러 처리**: 개별 큐 통계 조회 실패 시 {"error": str(e)} 반환

### **빠른 테스트 설정**
- **기본 테스트 타입**: ["cache", "database", "queue", "lock"] (request.test_types가 없을 때 사용)
- **사용자 지정 테스트**: request.test_types로 특정 테스트 지정 가능
- **테스트 결과 상태**: passed, failed, skipped, unknown
- **캐시 테스트**: admin_quick_test_cache 키 사용, 10초 TTL
- **데이터베이스 테스트**: "SELECT 1 as test" 쿼리 실행
- **락 테스트**: "admin_quick_test_lock" 키 사용

### **모니터링 설정**
- **service_monitor**: 런타임 모니터링 시스템 연동 (get_health_summary(), get_all_service_health() 메서드 사용)
- **psutil**: 시스템 리소스 모니터링 (import 시도, 실패 시 graceful fallback)
- **시스템 메트릭**: CPU, 메모리, 디스크, 네트워크 연결 수
- **서비스별 메트릭**: CacheService.get_metrics(), QueueService.get_stats(), SchedulerService.get_all_jobs_status()

## 🔗 연관 폴더

### **의존성 관계**
- **`service.db.database_service`**: DatabaseService - 데이터베이스 연결 상태 확인
- **`service.cache.cache_service`**: CacheService - Redis 연결 상태 및 기능 테스트
- **`service.lock.lock_service`**: LockService - 분산 락 서비스 상태 확인
- **`service.scheduler.scheduler_service`**: SchedulerService - 스케줄러 서비스 상태 및 작업 정보
- **`service.queue.queue_service`**: QueueService - 메시지 큐 및 이벤트 큐 통계 수집
- **`service.core.logger`**: Logger - 로깅 서비스
- **`service.core.service_monitor`**: service_monitor - 런타임 모니터링 시스템

### **기본 템플릿 연관**
- **`template.base.template.admin_template`**: AdminTemplate - 관리자 템플릿 기본 클래스
- **`template.base.client_session`**: ClientSession - 클라이언트 세션 관리
- **`template.base.template_service`**: TemplateService - 템플릿 서비스 관리

---
