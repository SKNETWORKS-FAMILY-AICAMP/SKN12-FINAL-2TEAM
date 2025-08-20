// 실제 채팅에서 서버 응답을 처리하는 유틸리티

export interface ServerChatResponse {
  session_id: string;
  reply: string | {
    content: string;
    chart: {
      symbols: string[];
      type: "mini" | "advanced";
      reason?: string;
    };
  };
}

export interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  chart?: {
    symbols: string[];
    type: "mini" | "advanced";
    reason?: string;
  };
}

/**
 * 서버 응답을 채팅 메시지 형식으로 변환합니다.
 */
export function parseServerResponse(
  response: ServerChatResponse, 
  messageId: string,
  timestamp: Date = new Date()
): ChatMessage {
  // 응답이 객체인지 문자열인지 확인
  if (typeof response.reply === "string") {
    // 일반 텍스트 응답
    return {
      id: messageId,
      role: "assistant",
      content: response.reply,
      timestamp
    };
  } else {
    // 차트 정보가 포함된 응답
    return {
      id: messageId,
      role: "assistant",
      content: response.reply.content,
      timestamp,
      chart: response.reply.chart
    };
  }
}

/**
 * 채팅 API 호출 함수
 */
export async function sendChatMessage(
  message: string, 
  sessionId?: string
): Promise<ServerChatResponse> {
  const accessToken = typeof window !== "undefined" ? localStorage.getItem("accessToken") : "";
  const sequence = Date.now();
  
  const payload = { 
    room_id: sessionId || "debug_room", 
    content: message, 
    include_portfolio: true,
    analysis_symbols: [],
    ai_persona: "GPT4O",
    accessToken: accessToken,
    sequence: sequence
  };

  const response = await fetch('/api/chat/message/send', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload)
  });

  if (!response.ok) {
    throw new Error('채팅 요청 실패');
  }

  const data = await response.json();
  
  // 실제 API 응답 구조에 맞게 변환
  if (data.errorCode === 0 && data.message) {
    return {
      session_id: sessionId || "debug_room",
      reply: data.message.content || data.message
    };
  } else {
    throw new Error(data.message || '채팅 요청 실패');
  }
}

/**
 * WebSocket을 통한 스트리밍 채팅 함수
 */
export function createStreamingChat(
  onMessage: (content: string) => void,
  onComplete: (fullResponse: ServerChatResponse) => void,
  onError: (error: string) => void
) {
  let ws: WebSocket | null = null;
  let fullContent = "";

  const connect = (sessionId?: string) => {
    ws = new WebSocket(`${process.env.NEXT_PUBLIC_WS_URL || 'wss://bullant-kr.com'}/ws/chat`);
    
    ws.onopen = () => {
      console.log('WebSocket 연결됨');
    };

    ws.onmessage = (event) => {
      const data = event.data;
      
      if (data === "[DONE]") {
        // 스트리밍 완료
        onComplete({
          session_id: sessionId || "",
          reply: fullContent
        });
        return;
      }

      // 스트리밍 데이터
      fullContent += data;
      onMessage(data);
    };

    ws.onerror = (error) => {
      console.error('WebSocket 에러:', error);
      onError('연결 오류가 발생했습니다.');
    };

    ws.onclose = () => {
      console.log('WebSocket 연결 종료');
    };
  };

  const sendMessage = (message: string, sessionId?: string) => {
    if (!ws || ws.readyState !== WebSocket.OPEN) {
      onError('연결이 끊어졌습니다.');
      return;
    }

    fullContent = ""; // 새 메시지 시작
    ws.send(JSON.stringify({
      message,
      session_id: sessionId || ""
    }));
  };

  const disconnect = () => {
    if (ws) {
      ws.close();
      ws = null;
    }
  };

  return {
    connect,
    sendMessage,
    disconnect
  };
}

/**
 * 차트 정보가 있는지 확인하는 함수
 */
export function hasChartInfo(response: ServerChatResponse): boolean {
  return typeof response.reply === "object" && 
         response.reply !== null && 
         "chart" in response.reply;
}

/**
 * 차트 정보를 추출하는 함수
 */
export function extractChartInfo(response: ServerChatResponse) {
  if (hasChartInfo(response)) {
    return (response.reply as any).chart;
  }
  return null;
}
