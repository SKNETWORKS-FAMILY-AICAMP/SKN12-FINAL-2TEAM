# ws_cli.py  ──────────────────────────────────────────
import asyncio, json, uuid, websockets

SESSION_ID = str(uuid.uuid4())          # 같은 방 유지
URI        = "ws://localhost:8000/stream"

async def ask_once(question: str):
    """질문 1회 → 토큰 스트림 출력"""
    async with websockets.connect(URI) as ws:
        # ① 전송
        await ws.send(json.dumps({
            "session_id": SESSION_ID,
            "message": question.strip()
        }))

        # ② 수신 (토큰 단위)
        full = ""
        async for msg in ws:
            if msg == "[DONE]":          # 서버가 끝낸 뒤 자동 close
                break
            print(msg, end="", flush=True)
            full += msg
        print("\n🤖 답변 완료\n")
        return full

async def main():
    try:
        while True:
            q = input("🙋 질문> ").strip()
            if q:
                await ask_once(q)
    except KeyboardInterrupt:
        print("\n🛑 종료")

if __name__ == "__main__":
    asyncio.run(main())
