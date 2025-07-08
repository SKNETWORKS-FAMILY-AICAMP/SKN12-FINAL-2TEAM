from .redis_cache_client import RedisCacheClient

class RedisCacheClientPool:
    """
    RedisCacheClient 인스턴스를 생성하는 풀 클래스.
    - app_id, env 등 네이밍 파라미터 사용
    - new() 메서드로 RedisCacheClient 인스턴스 반환
    """
    def __init__(self, host: str, port: int, session_expire_time: int, app_id: str, env: str, db: int = 0, password: str = ""):
        self._host = host
        self._port = port
        self._session_expire_time = session_expire_time
        self._app_id = app_id
        self._env = env
        self._db = db
        self._password = password

    def new(self) -> RedisCacheClient:
        """
        새로운 RedisCacheClient 인스턴스를 반환합니다.
        사용 예시:
            async with pool.new() as client:
                await client.set_string(...)
        """
        return RedisCacheClient(
            self._host,
            self._port,
            self._session_expire_time,
            self._app_id,
            self._env,
            self._db,
            self._password
        )
