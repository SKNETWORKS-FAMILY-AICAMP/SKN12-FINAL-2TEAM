from typing import Dict, Any, Optional
from service.core.logger import Logger
from .external_config import ExternalConfig
from .external_client_pool import ExternalClientPool, IExternalClientPool

class ExternalService:
    """External API 서비스 (정적 클래스) - 순수 라이브러리"""
    
    _config: Optional[ExternalConfig] = None
    _client_pool: Optional[IExternalClientPool] = None
    _initialized: bool = False
    
    @classmethod
    async def init(cls, config: ExternalConfig):
        """서비스 초기화"""
        cls._config = config
        cls._client_pool = ExternalClientPool(config)
        
        # 모든 API 클라이언트 사전 시작
        for api_name in config.apis.keys():
            client = cls._client_pool.new(api_name)
            await client.start()
            Logger.info(f"External client initialized for API: {api_name}")
            
        # Korea Investment 서비스 초기화 (있는 경우에만)
        if config.korea_investment:
            try:
                from service.external.korea_investment_service import KoreaInvestmentService
                from service.external.korea_investment_websocket_iocp import get_korea_investment_websocket
                from service.service_container import ServiceContainer
                
                ki_config = config.korea_investment
                if await KoreaInvestmentService.init(ki_config.app_key, ki_config.app_secret):
                    # REST API 연결 테스트 수행
                    health_result = await KoreaInvestmentService.health_check()
                    if health_result.get("healthy"):
                        Logger.info(f"✅ Korea Investment REST API 테스트 완료: {health_result.get('test_result', '')}")
                        
                        # WebSocket 서비스 초기화 및 테스트 - 무조건 성공해야 함
                        korea_websocket = await get_korea_investment_websocket()
                        
                        try:
                            ws_health_result = await korea_websocket.health_check(ki_config.app_key, ki_config.app_secret)
                            
                            # health_check는 이제 무조건 성공하거나 Exception 발생
                            Logger.info(f"✅ Korea Investment WebSocket 테스트 완료: {ws_health_result.get('test_result', '')}")
                            
                            # ServiceContainer에 등록
                            ServiceContainer.set_korea_investment_service(
                                KoreaInvestmentService, 
                                korea_websocket
                            )
                            Logger.info("✅ Korea Investment 서비스 (REST + WebSocket) 초기화 완료")
                            
                        except RuntimeError as ws_error:
                            Logger.error(f"❌ Korea Investment WebSocket 필수 연결 실패: {ws_error}")
                            Logger.error("🚨 WebSocket 연결이 필수입니다 - 서버 초기화 중단")
                            raise RuntimeError(f"Korea Investment WebSocket 연결 실패로 서버 시작 불가: {ws_error}")
                    else:
                        Logger.error(f"❌ Korea Investment REST API 테스트 실패: {health_result.get('error', '')}")
                else:
                    Logger.error("❌ Korea Investment 서비스 인증 실패")
            except Exception as e:
                Logger.error(f"❌ Korea Investment 서비스 초기화 실패: {e}")
            
        cls._initialized = True
        Logger.info("External service initialized")
        
    @classmethod
    async def shutdown(cls):
        """서비스 종료"""
        if cls._initialized and cls._client_pool:
            try:
                # 모든 클라이언트 강제 종료
                await cls._client_pool.close_all()
                
                # 조금 더 대기하여 모든 연결이 정리되도록 함
                import asyncio
                await asyncio.sleep(0.1)
                
            except Exception as e:
                Logger.error(f"External service shutdown error: {e}")
            finally:
                cls._client_pool = None
                cls._initialized = False
                Logger.info("External service shutdown")
            
    @classmethod
    def is_initialized(cls) -> bool:
        """초기화 여부 확인"""
        return cls._initialized
        
    @classmethod
    def get_client(cls, api_name: str):
        """특정 API 클라이언트 가져오기"""
        if not cls._initialized:
            raise RuntimeError("ExternalService not initialized")
        if not cls._client_pool:
            raise RuntimeError("ExternalService client pool not available")
        return cls._client_pool.new(api_name)
        
    # === 순수 API 요청 메서드 ===
    @classmethod
    async def request(cls, api_name: str, method: str, url: str, **kwargs) -> Dict[str, Any]:
        """일반 API 요청"""
        client = cls.get_client(api_name)
        return await client.request(method, url, **kwargs)
        
    @classmethod
    async def get(cls, api_name: str, url: str, **kwargs) -> Dict[str, Any]:
        """GET 요청"""
        client = cls.get_client(api_name)
        return await client.get(url, **kwargs)
        
    @classmethod
    async def post(cls, api_name: str, url: str, **kwargs) -> Dict[str, Any]:
        """POST 요청"""
        client = cls.get_client(api_name)
        return await client.post(url, **kwargs)
        
    @classmethod
    async def put(cls, api_name: str, url: str, **kwargs) -> Dict[str, Any]:
        """PUT 요청"""
        client = cls.get_client(api_name)
        return await client.request("PUT", url, **kwargs)
        
    @classmethod
    async def delete(cls, api_name: str, url: str, **kwargs) -> Dict[str, Any]:
        """DELETE 요청"""
        client = cls.get_client(api_name)
        return await client.request("DELETE", url, **kwargs)
    
    # === 모니터링 및 관리 메서드 ===
    @classmethod
    async def health_check(cls, api_name: Optional[str] = None) -> Dict[str, Any]:
        """Health Check - 특정 API 또는 전체 API 상태 확인"""
        if not cls._initialized:
            return {"healthy": False, "error": "Service not initialized"}
        
        if api_name:
            # 특정 API Health Check
            try:
                client = cls.get_client(api_name)
                return await client.health_check()
            except Exception as e:
                return {"healthy": False, "api": api_name, "error": str(e)}
        else:
            # 전체 API Health Check
            results = {}
            overall_healthy = True
            
            for api_name in cls._config.apis.keys():
                try:
                    client = cls.get_client(api_name)
                    result = await client.health_check()
                    results[api_name] = result
                    if not result.get("healthy", False):
                        overall_healthy = False
                except Exception as e:
                    results[api_name] = {"healthy": False, "error": str(e)}
                    overall_healthy = False
            
            return {
                "overall_healthy": overall_healthy,
                "apis": results,
                "total_apis": len(results)
            }
    
    @classmethod
    def get_metrics(cls, api_name: Optional[str] = None) -> Dict[str, Any]:
        """메트릭 조회 - 특정 API 또는 전체 API 메트릭"""
        if not cls._initialized:
            return {"error": "Service not initialized"}
        
        if api_name:
            # 특정 API 메트릭
            try:
                client = cls.get_client(api_name)
                return client.get_metrics()
            except Exception as e:
                return {"error": str(e), "api": api_name}
        else:
            # 전체 API 메트릭
            results = {}
            total_requests = 0
            total_successes = 0
            total_failures = 0
            
            for api_name in cls._config.apis.keys():
                try:
                    client = cls.get_client(api_name)
                    metrics = client.get_metrics()
                    results[api_name] = metrics
                    
                    total_requests += metrics.get("total_requests", 0)
                    total_successes += metrics.get("successful_requests", 0)
                    total_failures += metrics.get("failed_requests", 0)
                except Exception as e:
                    results[api_name] = {"error": str(e)}
            
            overall_success_rate = 0.0
            if total_requests > 0:
                overall_success_rate = total_successes / total_requests
            
            return {
                "overall_metrics": {
                    "total_requests": total_requests,
                    "successful_requests": total_successes,
                    "failed_requests": total_failures,
                    "success_rate": overall_success_rate
                },
                "api_metrics": results,
                "total_apis": len(cls._config.apis)
            }
    
    @classmethod
    def reset_metrics(cls, api_name: Optional[str] = None):
        """메트릭 리셋 - 특정 API 또는 전체 API"""
        if not cls._initialized:
            Logger.warn("Cannot reset metrics: Service not initialized")
            return
        
        if api_name:
            # 특정 API 메트릭 리셋
            try:
                client = cls.get_client(api_name)
                client.reset_metrics()
                Logger.info(f"Metrics reset for API: {api_name}")
            except Exception as e:
                Logger.error(f"Failed to reset metrics for API {api_name}: {e}")
        else:
            # 전체 API 메트릭 리셋
            reset_count = 0
            for api_name in cls._config.apis.keys():
                try:
                    client = cls.get_client(api_name)
                    client.reset_metrics()
                    reset_count += 1
                except Exception as e:
                    Logger.error(f"Failed to reset metrics for API {api_name}: {e}")
            
            Logger.info(f"Metrics reset for {reset_count}/{len(cls._config.apis)} APIs")