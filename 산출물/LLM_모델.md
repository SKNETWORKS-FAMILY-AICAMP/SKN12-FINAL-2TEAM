# **LLM 활용 소프트웨어 제출 문서**
> GPT-4o mini 기반 AI 채팅형 금융 분석 플랫폼


## 목차
1. [시스템 개요](#시스템-개요)  
2. [전체 아키텍처](#전체-아키텍처)  
   - 2-1. Layer 1 – Service & Entry  
   - 2-2. Layer 2 – Router & Orchestrator  
   - 2-3. Layer 3 – Tool Ecosystem  
   - 2-4. Layer 4 – Abstraction & Foundation  
   - 2-5. Async Persistence & Storage  
3. [핵심 코드 스크린샷](#핵심-코드-스크린샷)  
4. [LLM 호출 · Tool 라우팅 흐름](#llm-호출--tool-라우팅-흐름)  
5. [맺음말](#맺음말)

---

## 시스템 개요
이 플랫폼은 **GPT-4o mini** LLM을 **의도 분류**와 **도구(Tool) 선택**에 활용하여  
약 **12종**의 금융 분석 도구를 결합, **대화형 금융 리포트·분석**을 실시간으로 생성합니다.

- 사용자가 자연어로 질문 →  
- LLM이 의도를 분석 →  
- **LangGraph Router**가 알맞은 Tool(기본/고급)을 실행 →  
- 실행 결과를 종합해 **전문 답변**을 반환

---

## 아키텍쳐 아키텍처

>
> ![](https://velog.velcdn.com/images/cpldxx/post/d18abd18-c630-49c6-9c3e-a48270cf01ce/image.png)

### 2-1. Layer 1 – Service & Entry
| 파일/컴포넌트 | 역할 |
|---|---|
| **`AIChat_service.py`** | REST `POST /message/send` & WS `/stream` 수신, 세션 관리 |
| **Redis** | 최근 N개 메시지, 토큰 사용량 캐시 |

### 2-2. Layer 2 – Router & Orchestrator
| 컴포넌트 | 역할 |
|---|---|
| **AIChat Router (LangGraph)** | LLM 호출 → Tool 선택/실행 워크플로 제어 |
| **GPT-4o mini** | 의도 분류, Tool 파라미터 추론, 최종 답변 초안 생성 |

### 2-3. Layer 3 – Tool Ecosystem
- **Basic Tools (`AIChat/BasicTools/`)**  
  외부 API(FMP, gNews, FRED, yfinance, ta 등) 호출: RSI, 재무제표, 뉴스, 거시지표 등 단일 기능
- **Advanced Tools (`AIChat/tool/`)**  
  MarketRegimeDetectorTool, BlackLittermanOptimizerTool, DynamicVaRModelTool, MLSignalEnsembleTool 등 복합 분석/ML  
  *(현황: MarketRegimeDetector, KalmanFilter 구현 완료 — 폴리싱 필요)*

### 2-4. Layer 4 – Abstraction & Foundation
- `BaseFinanceTool` 추상 클래스(ABC): 모든 Tool이 상속, `get_data()` 표준 인터페이스 제공

### 2-5. Async Persistence & Storage
| 구성요소 | 설명 |
|---|---|
| `MessageQueue` | Service → Consumer 비동기 전달 |
| `ChatPersistenceConsumer` | 3초 또는 50건 단위 배치 → MySQL 저장 |
| `MessageStateMachine` | COMPOSING → SENT 등 상태 전이/추적 |
| `DistributedLock` | room ID 기반 순서 보장 |
| `MySQL` | 영구 채팅 로그 저장 |

---

## 핵심 코드 스크린샷

### 3.1. `base_server/service/llm/AIChat_service.py`
- REST: `/message/send` 처리
- WebSocket: `/stream` 처리
- Redis 캐시(세션별 대화 기록)
- LLM 연동: Router를 통해 Tool 호출

> <img width="472" height="555" alt="image" src="https://github.com/user-attachments/assets/3631783d-1de3-430e-93ba-32a1656dea00" />



---

### 3.2. `base_server/service/llm/AIChat/Router.py`
- 사용자 질문 분석 및 도구 선택(LLM)
- LangGraph 노드: `tool_selector` / `run_tool`
- 선택된 Tool 실행 및 외부 API 호출
- 상태 기반 워크플로 제어

> <img width="472" height="685" alt="image" src="https://github.com/user-attachments/assets/5c65995d-d763-4436-8aa4-fd832594646a" />


---

### 3.3. `base_server/service/llm/AIChat/BaseFinanceTool.py`
- 모든 금융 도구의 베이스 클래스
- `get_data()` 추상 메서드로 표준화

> ![](https://velog.velcdn.com/images/cpldxx/post/ee48a9f2-7b16-4b5d-b0b6-caa503ee5b3b/image.png)

---

### 3.4. `base_server/service/llm/AIChat/tool/MarketRegimeDetectorTool.py`
- Layer 3 – Advanced Tools
- 여러 Basic Tool을 조합해 시장 국면(Bull/Bear/Sideways) 감지
- Bayesian + HMM 기반 분석
- `BaseFinanceTool` 상속

> <img width="471" height="673" alt="image" src="https://github.com/user-attachments/assets/cab57be3-04a0-499d-9bad-2e2cff0bfafa" />


---

### 3.5. `base_server/service/queue/message_queue.py`
- Service → Consumer 비동기 전달
- 우선순위/재시도/지연 실행 지원

> <img width="473" height="358" alt="image" src="https://github.com/user-attachments/assets/b276bb1d-68b8-45a4-a8ae-4ab57a6e2946" />



---

### 3.6. `base_server/template/chat/chat_persistence_consumer.py`
- 3초·50건 배치 저장 루프
- Redis → MySQL 영구 저장
- 카카오톡 방식 비동기 처리

> <img width="473" height="534" alt="image" src="https://github.com/user-attachments/assets/0a01e587-5429-4e3f-85da-9bc8b143db1b" />


---

### 3.7. `base_server/template/chat/chat_state_machine.py`
- COMPOSING → SENT 상태 전이 관리
- Redis 기반 원자적 상태 관리
- 분산 환경에서 안전한 상태 추적

> <img width="474" height="464" alt="image" src="https://github.com/user-attachments/assets/5e86c986-199d-47a2-8ddc-16b8e1e73c2d" />


---

## LLM 호출 · Tool 라우팅 흐름

```text
클라이언트 → /message/send (REST) 또는 /stream (WS)
        │
        ▼
AIChat_service.py (Layer 1, 세션/캐시 관리)
        │
        ▼
LangGraph Router (Layer 2)
        │ ① LLM에 의도 분석 요청
        ▼
GPT-4o mini ──> {tool, args} 반환
        │
        ▼
선택된 Tool 실행 (Layer 3, Basic/Advanced → 외부 API)
        │
        ▼
Router가 결과 수집 → LLM이 최종 답변 초안 생성
        │
        ▼
스트리밍 응답 전송, Redis/Queue로 비동기 영구 저장

```
---
### 맺음말
- LLM 분류 + LangGraph 라우팅 + 모듈형 Tool 구조로 기능 확장이 용이
- 비동기 배치 저장으로 카카오톡 수준의 채팅 일관성·신뢰성 확보
- 모델 교체 시 llm_config.py 와 models/ 폴더만 바꾸면 바로 적용 가능
