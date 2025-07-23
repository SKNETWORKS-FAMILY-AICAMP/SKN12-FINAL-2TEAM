import asyncio
import redis.asyncio as redis 

async def main():
    # self.redis 대신 새로 연결해도 되고, 메서드 안이면 self.redis 바로 사용해도 됩니다.
    r = redis.Redis(host="localhost", port=6379, decode_responses=True)
    info = await r.info("server")          # 서버 섹션만 가져오기
    print("Redis server version =", info["redis_version"])

asyncio.run(main())