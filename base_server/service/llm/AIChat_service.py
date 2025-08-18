# base_server/service/llm/AIChat_service.py

from service.core.logger import Logger
import os, uuid, asyncio, json
from fastapi import WebSocket, WebSocketDisconnect, HTTPException
from langchain.memory import ConversationBufferMemory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_core.prompts import ChatPromptTemplate

from service.service_container import ServiceContainer
from service.cache.cache_service import CacheService
from service.llm.AIChat.Router import AIChatRouter
from service.llm.llm_config import LlmConfig
from markdown import markdown
class AIChatService:
    """AI 채팅 서비스 - LLM 응답 생성에만 집중"""
    def __init__(self, llm_config: LlmConfig):
        self.llm_config = llm_config
        # llm 인스턴스는 llm_config에서 직접 생성
        from langchain_openai import ChatOpenAI
        api_key = os.getenv("OPENAI_API_KEY") or llm_config.providers[llm_config.default_provider].api_key
        self.llm = ChatOpenAI(model=llm_config.providers[llm_config.default_provider].model,
                              temperature=llm_config.providers[llm_config.default_provider].temperature,
                              openai_api_key=api_key)
        # 스트리밍용 LLM
        self.llm_stream = ChatOpenAI(model=llm_config.providers[llm_config.default_provider].model,
                                     temperature=llm_config.providers[llm_config.default_provider].temperature,
                                     streaming=True,
                                     openai_api_key=api_key)
        self._session_mem: dict[str, ConversationBufferMemory] = {}

        if not CacheService.is_initialized():
            raise RuntimeError("CacheService is not initialized. Please initialize CacheService first.")

        self.cache_service = CacheService.get_instance()
        # CacheService의 네임스페이스를 가져와서 사용
        cache_client = self.cache_service.get_client()
        # RedisChatMessageHistory의 key_prefix에 네임스페이스 포함
        # 주의: RedisChatMessageHistory는 key_prefix와 session_id를 조합하여 키를 생성
        # 실제 키: {key_prefix}{session_id}
        self.KEY_PREFIX = f"{cache_client.cache_key}:chat:"
        Logger.info(f"AIChatService initialized with key prefix: {self.KEY_PREFIX}")

    def mem(self, session_id: str) -> ConversationBufferMemory:
        """세션별 대화 메모리 관리 (Redis 기반)"""
        if session_id not in self._session_mem:
            cache_client = self.cache_service.get_client()
            redis_url = f"redis://{cache_client._host}:{cache_client._port}/{cache_client._db}"
            if cache_client._password:
                redis_url = f"redis://:{cache_client._password}@{cache_client._host}:{cache_client._port}/{cache_client._db}"
            
            # RedisChatMessageHistory는 key_prefix + session_id로 키를 생성
            # 예: finance_app:LOCAL:chat:room_123 형태로 저장됨
            history = RedisChatMessageHistory(
                session_id=session_id,
                url=redis_url,
                key_prefix=self.KEY_PREFIX,  # finance_app:LOCAL:chat:
            )
            
            # 디버깅을 위한 로그 추가
            Logger.debug(f"Creating RedisChatMessageHistory with key_prefix={self.KEY_PREFIX}, session_id={session_id}")
            Logger.debug(f"Expected Redis key pattern: {self.KEY_PREFIX}{session_id}")
            
            self._session_mem[session_id] = ConversationBufferMemory(
                chat_memory=history,
                return_messages=True
            )
        return self._session_mem[session_id]

    async def chat(self, message: str, session_id: str = "", client_session=None):
        """REST API용 채팅 응답 생성"""
        if not message.strip():
            raise HTTPException(400, "message empty")
        sid = session_id or str(uuid.uuid4())
        Logger.debug(f"AIChatService.chat called with session_id={sid}, message={message}")
        
        # 🆕 세션 정보를 포함한 라우터 생성
        Logger.debug(f"AIChatService.chat client_session: {client_session}")
        router = AIChatRouter(client_session)
        
        # 🆕 클로저로 안전하게 감싸기 (비동기 처리 안전성)
        def run_question_with_session():
            return router.run_question(message)
        
        # 비동기 실행으로 변경하여 도구 호출이 제대로 작동하도록 함
        loop = asyncio.get_event_loop()
        tool_out = await loop.run_in_executor(None, run_question_with_session)
        answer = await self._full_answer(sid, message, tool_out)
        Logger.debug(f"AIChatService.chat response for session_id={sid}: {answer}")
        return {"session_id": sid, "reply": answer}

    async def stream(self, ws: WebSocket):
        """WebSocket용 스트리밍 채팅 응답 생성"""
        await ws.accept()
        try:
            while True:
                data = await ws.receive_text()
                try:
                    req = json.loads(data)
                    q = req["message"].strip()
                    sid = req.get("session_id") or str(uuid.uuid4())
                except (KeyError, json.JSONDecodeError):
                    await ws.send_text(json.dumps({"error": "bad payload"}))
                    continue
                if not q:
                    await ws.send_text(json.dumps({"error": "empty message"}))
                    continue

                router = AIChatRouter()
                tool_out = await asyncio.get_running_loop().run_in_executor(
                    None, router.run_question, q
                )
                joined = "\n".join(tool_out) if isinstance(tool_out, list) else str(tool_out)

                memory = self.mem(sid)
                prompt = ChatPromptTemplate.from_messages(
                    [("system", "당신은 친절하고 정확한 AI 비서입니다.")] +
                    memory.buffer +
                    [("user", f'{q}\n\n🛠 도구 결과:\n{joined}')]
                )

                stream = (prompt | self.llm_stream).astream({})
                full_resp = ""
                async for chunk in stream:
                    token = getattr(chunk, "content", "")
                    if token:
                        full_resp += token
                        await ws.send_text(token)
                await ws.send_text("[DONE]")
                memory.chat_memory.add_user_message(q)
                memory.chat_memory.add_ai_message(full_resp)
        except WebSocketDisconnect:
            return

    async def _full_answer(self, sid: str, question: str, tool_out):
        """전체 응답 생성 (REST API용)"""
        joined = "\n".join(tool_out) if isinstance(tool_out, list) else str(tool_out)
        memory = self.mem(sid)
        
        # 차트 정보를 포함한 시스템 프롬프트
        system_prompt = """당신은 친절하고 정확한 AI 비서입니다.

🚫 **절대 금지 규칙: 금융/투자/경제 관련 질문이 아니면 무조건 차단!**

🚨 **금융 외 질문 키워드 감지 시 즉시 차단:**
운세, 띠, 별자리, 사주, 타로, 점성술, 연애, 사랑, 요리, 음식, 날씨, 게임, 영화, 음악, 운동, 여행, 교육, 학업 등이 포함된 질문은 즉시 차단하고 금융 질문만 요청하라!

❌ **금융 외 질문 차단 목록 (절대 답변 금지):**
- 운세, 사주, 타로, 점성술, 띠, 별자리, 오늘의 운세
- 사랑, 연애, 인간관계 고민, 연애운
- 요리, 음식, 레시피, 맛집
- 날씨, 기후, 계절, 일기예보
- 게임, 엔터테인먼트, 영화, 음악, 드라마
- 운동, 건강 관리, 다이어트, 다이어트 방법
- 여행, 관광, 문화, 축제
- 교육, 학습, 학업, 공부법
- 기타 금융/투자/경제와 무관한 모든 질문

⚠️ **중요:**
- 사용자의 질문이 금융/투자/경제 관련인지 먼저 판단해. 관련이 없으면 즉시 차단하고 금융 질문만 요청해.
- 운세, 띠, 별자리, 사주, 사랑, 요리, 날씨, 게임, 영화, 음악, 운동 등 금융 외 모든 질문은 무조건 차단.
- 질문에 '운세', '띠', '사주', '사랑', '요리', '날씨', '게임', '영화' 등이 포함되면 즉시 차단.

주식 관련 질문에 답할 때는 다음과 같은 형식으로 응답해주세요:

1. 일반적인 답변 후
2. 차트 정보를 JSON 형식으로 포함:

```chart
{{
  "symbols": ["NASDAQ:TSLA"],
  "type": "mini",
  "reason": "테슬라 주식 분석"
}}
```

차트 타입:
- "mini": 간단한 차트 (일반적인 주식 대화)
- "advanced": 고급 차트 (기술적 분석, 지표 등)

**주식 관련 질문 감지 규칙:**
- 질문에 주식 심볼(AAPL, TSLA, MSFT 등)이 언급되면 차트 정보 포함
- "주식", "주가", "차트", "분석", "기술적", "재무" 등 키워드가 있으면 차트 정보 포함
- 일반적인 경제/투자 질문이면 차트 정보 포함

**차트 심볼 매핑:**
- 애플 → "NASDAQ:AAPL"
- 테슬라 → "NASDAQ:TSLA"
- 마이크로소프트 → "NASDAQ:MSFT"
- 구글 → "NASDAQ:GOOGL"
- 아마존 → "NASDAQ:AMZN"
- 엔비디아 → "NASDAQ:NVDA"
- 메타 → "NASDAQ:META"
- 넷플릭스 → "NASDAQ:NFLX"

미국 주식에 대해서만 정보를 제공해.

예시:
사용자: "애플 주식 어때?"
답변: "애플(AAPL) 주식은 현재 상승 추세에 있습니다...

```chart
{{
  "symbols": ["NASDAQ:AAPL"],
  "type": "mini",
  "reason": "애플 주식 분석"
}}
```

사용자: "테슬라와 엔비디아 기술적 분석해줘"
답변: "테슬라와 엔비디아의 기술적 분석 결과입니다...

```chart
{{
  "symbols": ["NASDAQ:TSLA", "NASDAQ:NVDA"],
  "type": "advanced",
  "reason": "테슬라와 엔비디아 기술적 분석"
}}
```

사용자: "날씨 어때?"
답변: "🚫 **금융 투자 상담 외의 질문은 답변할 수 없습니다. 주식, 투자, 경제 관련 질문만 해주세요.**"

사용자: "요리법 알려줘"
답변: "🚫 **금융 투자 상담 외의 질문은 답변할 수 없습니다. 주식, 투자, 경제 관련 질문만 해주세요.**"

사용자: "운세 알려줘"
답변: "🚫 **금융 투자 상담 외의 질문은 답변할 수 없습니다. 주식, 투자, 경제 관련 질문만 해주세요.**" """

        prompt = ChatPromptTemplate.from_messages(
            [("system", system_prompt)] +
            memory.buffer +
            [("user", f'{question}\n\n🛠 도구 결과:\n{joined}')]
        )
        
        raw_answer = (prompt | self.llm).invoke({}).content
        
        # 차트 정보 추출 (LLM 응답과 원본 질문 모두 확인)
        chart_info = self._extract_chart_info(raw_answer)
        Logger.debug(f"LLM 응답에서 추출한 차트 정보: {chart_info}")
        
        if not chart_info:
            # LLM 응답에 차트 정보가 없으면 원본 질문에서 추출
            chart_info = self._extract_stock_symbols_from_question(question)
            Logger.debug(f"원본 질문에서 추출한 차트 정보: {chart_info}")
        
        Logger.debug(f"최종 차트 정보: {chart_info}")
        
        # 금융 외 질문인 경우 차트 정보 제거
        if self._is_non_financial_question(question):
            chart_info = None
            Logger.debug("금융 외 질문으로 판단되어 차트 정보 제거")
        
        # 마크다운 변환 (차트 정보 제외)
        answer_without_chart = self._remove_chart_info(raw_answer)
        answer = markdown(answer_without_chart)
        
        if isinstance(answer, list):
            answer = "\n".join(str(x) for x in answer)
        
        memory.chat_memory.add_user_message(question)
        memory.chat_memory.add_ai_message(answer_without_chart)
        
        # 차트 정보가 있으면 포함하여 반환
        if chart_info:
            return {
                "content": answer,
                "chart": chart_info
            }
        else:
            return answer

    def _extract_chart_info(self, text: str) -> dict | None:
        """텍스트에서 차트 정보를 추출합니다."""
        import re
        import json
        
        # ```chart ... ``` 패턴 찾기
        chart_pattern = r'```chart\s*\n(.*?)\n```'
        match = re.search(chart_pattern, text, re.DOTALL)
        
        if match:
            try:
                chart_json = match.group(1).strip()
                chart_info = json.loads(chart_json)
                
                # 필수 필드 검증
                if "symbols" in chart_info and "type" in chart_info:
                    Logger.debug(f"Extracted chart info: {chart_info}")
                    return chart_info
                else:
                    Logger.warn(f"Invalid chart info format: {chart_info}")
                    return None
            except json.JSONDecodeError as e:
                Logger.warn(f"Failed to parse chart JSON: {e}")
                return None
        
        # 차트 정보가 없으면 질문에서 주식 심볼을 추출하여 기본 차트 정보 생성
        return self._extract_stock_symbols_from_question(text)
    
    def _extract_stock_symbols_from_question(self, text: str) -> dict | None:
        """질문에서 주식 심볼을 추출하여 기본 차트 정보를 생성합니다."""
        import re
        
        # 주식 심볼 매핑
        stock_mapping = {
            '애플': 'NASDAQ:AAPL', 'apple': 'NASDAQ:AAPL', 'aapl': 'NASDAQ:AAPL',
            '테슬라': 'NASDAQ:TSLA', 'tesla': 'NASDAQ:TSLA', 'tsla': 'NASDAQ:TSLA',
            '마이크로소프트': 'NASDAQ:MSFT', 'microsoft': 'NASDAQ:MSFT', 'msft': 'NASDAQ:MSFT',
            '구글': 'NASDAQ:GOOGL', 'google': 'NASDAQ:GOOGL', 'googl': 'NASDAQ:GOOGL',
            '아마존': 'NASDAQ:AMZN', 'amazon': 'NASDAQ:AMZN', 'amzn': 'NASDAQ:AMZN',
            '엔비디아': 'NASDAQ:NVDA', 'nvidia': 'NASDAQ:NVDA', 'nvda': 'NASDAQ:NVDA',
            '메타': 'NASDAQ:META', 'meta': 'NASDAQ:META', 'meta': 'NASDAQ:META',
            '넷플릭스': 'NASDAQ:NFLX', 'netflix': 'NASDAQ:NFLX', 'nflx': 'NASDAQ:NFLX',
            '삼성전자': 'KRX:005930', '삼성': 'KRX:005930',
            'sk하이닉스': 'KRX:000660', 'sk': 'KRX:000660',
            '현대차': 'KRX:005380', '현대': 'KRX:005380',
            'lg에너지솔루션': 'KRX:373220', 'lg에너지': 'KRX:373220'
        }
        
        # 질문에서 주식 심볼 찾기
        found_symbols = []
        question_lower = text.lower()
        
        for keyword, symbol in stock_mapping.items():
            if keyword.lower() in question_lower:
                found_symbols.append(symbol)
        
        # 중복 제거
        found_symbols = list(set(found_symbols))
        
        if found_symbols:
            # 차트 타입 결정
            chart_type = "advanced" if any(word in question_lower for word in ["기술적", "분석", "지표", "rsi", "macd"]) else "mini"
            
            chart_info = {
                "symbols": found_symbols,
                "type": chart_type,
                "reason": f"{', '.join([s.split(':')[1] for s in found_symbols])} 주식 분석"
            }
            
            Logger.debug(f"Auto-generated chart info: {chart_info}")
            return chart_info
        
        return None
    
    def _is_non_financial_question(self, text: str) -> bool:
        """질문이 금융 외 질문인지 판단합니다."""
        non_financial_keywords = [
            '운세', '띠', '별자리', '사주', '타로', '점성술', '오늘의 운세',
            '사랑', '연애', '인간관계', '연애운', '고민',
            '요리', '음식', '레시피', '맛집',
            '날씨', '기후', '계절', '일기예보',
            '게임', '엔터테인먼트', '영화', '음악', '드라마',
            '운동', '건강', '다이어트', '다이어트 방법',
            '여행', '관광', '문화', '축제',
            '교육', '학습', '학업', '공부법'
        ]
        
        text_lower = text.lower()
        for keyword in non_financial_keywords:
            if keyword in text_lower:
                Logger.debug(f"금융 외 질문 감지: '{keyword}' 키워드 발견")
                return True
        
        return False

    def _remove_chart_info(self, text: str) -> str:
        """텍스트에서 차트 정보를 제거합니다."""
        import re
        
        # ```chart ... ``` 패턴 제거
        chart_pattern = r'```chart\s*\n.*?\n```'
        cleaned_text = re.sub(chart_pattern, '', text, flags=re.DOTALL)
        
        return cleaned_text.strip()

    async def load_chat_history(self, session_id: str, messages: list):
        """DB/Redis에서 로드한 채팅 히스토리를 메모리에 복원
        
        Args:
            session_id: 채팅 세션 ID (room_id)
            messages: ChatMessage 객체 리스트 (시간순 정렬됨)
        """
        try:
            memory = self.mem(session_id)
            
            # 메모리가 이미 있는지 다시 한번 확인 (안전장치)
            if len(memory.buffer) > 0:
                Logger.debug(f"Memory already exists for session {session_id}, skipping history load")
                return
            
            # 메시지가 없으면 로드할 필요 없음
            if not messages:
                Logger.debug(f"No messages to load for session {session_id}")
                return
            
            # 메시지를 시간순으로 메모리에 추가 (clear 하지 않고 추가만)
            loaded_count = 0
            for msg in messages:
                try:
                    if msg.sender_type == "USER":
                        memory.chat_memory.add_user_message(msg.content)
                        loaded_count += 1
                    elif msg.sender_type == "AI":
                        memory.chat_memory.add_ai_message(msg.content)
                        loaded_count += 1
                    else:
                        Logger.debug(f"Skipping message with unknown sender_type: {msg.sender_type}")
                except Exception as msg_error:
                    Logger.warn(f"Failed to load message {msg.message_id}: {msg_error}")
                    continue
            
            Logger.info(f"Loaded {loaded_count}/{len(messages)} messages into AI memory for session {session_id}")
            
        except Exception as e:
            Logger.error(f"Failed to load chat history for session {session_id}: {e}")
            # 히스토리 로드 실패해도 계속 진행 (새 대화로 시작)
    
    async def get_session_memory_keys(self, session_id: str) -> list:
        """특정 세션의 Redis 키 패턴 반환 (디버깅용)
        
        Returns:
            실제 Redis에 저장되는 키 리스트
        """
        # RedisChatMessageHistory의 기본 키 패턴
        # LangChain은 보통 {key_prefix}{session_id} 형태로 키를 생성
        base_key = f"{self.KEY_PREFIX}{session_id}"
        
        # LangChain의 일반적인 패턴
        return [
            base_key,  # 메인 키
            f"{base_key}:messages",  # 메시지 리스트 (가능한 패턴)
        ]

    async def do_with_lock(self, key: str, ttl: int = 10):
        """분산 락을 사용한 작업 실행"""
        lock_service = ServiceContainer.get_lock_service()
        token = await lock_service.acquire(key, ttl=ttl)
        if not token:
            raise Exception("락 획득 실패")
        try:
            # 락이 보장된 작업
            pass
        finally:
            await lock_service.release(key, token)
