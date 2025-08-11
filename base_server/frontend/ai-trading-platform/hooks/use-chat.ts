"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { apiClient } from "@/lib/api/client"
import { handleApiError, getErrorMessage } from "@/lib/error-handler"

interface LocalMessage {
  id: string;
  content: string;
  role: "user" | "assistant";
  isTyping?: boolean;
  timestamp?: number; // 추가: 메시지 생성 시간
}

export function useChat() {
  const [rooms, setRooms] = useState<any[]>([]);
  const [currentRoomId, setCurrentRoomId] = useState<string | null>(null);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected_persona, setSelected_persona] = useState<string>("GPT4O");
  const [personas, setPersonas] = useState<any[]>([]);
  const [typingMessageId, setTypingMessageId] = useState<string | null>(null);
  const [messageCounter, setMessageCounter] = useState(0); // 메시지 개수 추적

  // 고유 ID 생성 함수
  const generateUniqueId = useCallback((prefix: string) => {
    return `${prefix}_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
  }, []);

  // 채팅방 목록 불러오기 (사용자 액션 기반)
  const loadRooms = useCallback(async () => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await apiClient.post("/api/chat/rooms", {
        page: 1,
        limit: 20
      }) as any
      
      if (response.errorCode === 0) {
        setRooms(response.rooms || [])
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError(errorMessage)
      }
    } catch (e: any) {
      // 공통 에러 처리 사용
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        // 세션 만료 시 에러 상태만 설정 (리다이렉트는 자동 처리됨)
        setError("세션이 만료되어 로그인 페이지로 이동합니다.")
        return
      }
      
      setError(errorInfo.message)
      console.error("채팅방 목록 불러오기 실패:", e)
    } finally {
      setIsLoading(false)
    }
  }, [])

  // 메시지 목록 불러오기 (사용자 액션 기반)
  const loadMessages = useCallback(async (roomId: string) => {
    setIsLoading(true)
    setError(null)
    
    try {
      const response = await apiClient.post(`/api/chat/messages`, {
        room_id: roomId,
        page: 1,
        limit: 50
      }) as any
      
      // 백엔드 응답 구조 디버깅
      console.log("[useChat] 메시지 목록 응답:", response);
      console.log("[useChat] 메시지 목록 구조:", {
        errorCode: response.errorCode,
        messages: response.messages,
        messagesCount: response.messages ? response.messages.length : 0
      });
      
      if (response.errorCode === 0) {
        // 백엔드 응답을 UI 메시지로 정규화 (백엔드 ID 우선 사용)
        const normalizedMessages = (response.messages || []).map((m: any) => ({
          id: m.message_id, // 백엔드에서 생성한 고유 ID 우선 사용
          role: m.sender_type === 'USER' ? 'user' : 'assistant',
          content: m.content,
          timestamp: m.timestamp || m.created_at || Date.now()
        }));
        
        console.log("[useChat] 정규화된 메시지:", normalizedMessages);
        setMessages(normalizedMessages)
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError(errorMessage)
      }
    } catch (error: any) {
      if (error.code === 'ECONNABORTED') {
        setError('요청 시간이 초과되었습니다. 다시 시도해주세요.');
      } else {
        setError('메시지 목록을 불러오는데 실패했습니다.');
      }
      console.error("[useChat] loadMessages 에러:", error);
    } finally {
      setIsLoading(false)
    }
  }, []);

  // 에러 초기화
  const clearError = useCallback(() => {
    setError(null);
  }, []);

  // 초기 로딩 (컴포넌트 마운트 시 한 번만)
  useEffect(() => {
    loadRooms();
    
    // 페르소나 목록 초기화 (로컬 SVG 이미지 사용)
    setPersonas([
      { 
        persona_id: "GPT4O", 
        name: "GPT-4o", 
        description: "범용 AI 어시스턴트",
        avatar_url: "/images/ai-avatar-gpt.svg"
      },
      { 
        persona_id: "market_analysis", 
        name: "시장 분석가", 
        description: "주식 시장 분석 및 예측",
        avatar_url: "/images/ai-avatar-analyst.svg"
      },
      { 
        persona_id: "stock_screener", 
        name: "종목 스크리너", 
        description: "투자 가치가 높은 종목 발굴",
        avatar_url: "/images/ai-avatar-screener.svg"
      },
      { 
        persona_id: "portfolio_optimizer", 
        name: "포트폴리오 최적화", 
        description: "투자 포트폴리오 최적화",
        avatar_url: "/images/ai-avatar-portfolio.svg"
      },
      { 
        persona_id: "trading_signals", 
        name: "트레이딩 시그널", 
        description: "매수/매도 타이밍 신호",
        avatar_url: "/images/ai-avatar-signals.svg"
      }
    ]);
  }, [loadRooms]);

  // 현재 채팅방이 변경되면 메시지 로드
  useEffect(() => {
    if (currentRoomId) {
      loadMessages(currentRoomId);
    }
  }, [currentRoomId, loadMessages]);

  // 메시지 전송 (사용자 액션 기반)
  const sendMessage = useCallback(async (content: string, personaOverride?: string) => {
    const roomIdToUse = currentRoomId || "test_room";
    const persona = personaOverride || selected_persona || "GPT4O"; // 선택된 페르소나
    setIsLoading(true);
    
    // 임시 사용자 메시지 ID 생성 (백엔드 응답으로 교체될 예정)
    const tempUserId = generateUniqueId('temp_user');
    
    // 임시 사용자 메시지 추가 (백엔드 응답으로 교체될 예정)
    setMessages(prev => [
      ...prev,
      { id: tempUserId, content, role: "user", timestamp: Date.now() }
    ]);
    
    try { // 메시지 전송
      let res = await apiClient.post(`/api/chat/message/send`, { room_id: roomIdToUse, content, ai_persona: persona });
      let parsed: any = res;
      if (parsed && parsed.data && typeof parsed.data === "object") {
        parsed = parsed.data;
      }
      
      // 백엔드 응답 구조 디버깅
      console.log("[useChat] 백엔드 응답 전체:", parsed);
      console.log("[useChat] 백엔드 응답 구조:", {
        errorCode: parsed.errorCode,
        message: parsed.message,
        messageKeys: parsed.message ? Object.keys(parsed.message) : []
      });
      
      if (parsed.errorCode === 0) {
        // 백엔드 응답에서 AI 메시지 정보 추출
        const messageObj = parsed.message; // AI 메시지 정보
        
        if (messageObj && messageObj.content) {
          // 1. 임시 사용자 메시지를 고유 ID로 교체 (백엔드에서 user_message_id를 별도로 보내지 않음)
          const userMessageId = generateUniqueId('user');
          setMessages(prev => prev.map(msg => 
            msg.id === tempUserId 
              ? { ...msg, id: userMessageId, timestamp: Date.now() }
              : msg
          ));
          
          // 2. AI 메시지 추가 (백엔드에서 생성한 message_id 사용)
          const aiMessageId = messageObj.message_id;
          const aiMessage: LocalMessage = {
            id: aiMessageId,
            content: messageObj.content,
            role: "assistant",
            timestamp: messageObj.timestamp || messageObj.created_at || Date.now()
          };
          
          console.log("[useChat] AI 메시지 추가:", aiMessage);
          setMessages(prev => [...prev, aiMessage]);
          
          // 3. 메시지 카운터 증가
          setMessageCounter(prev => prev + 2); // 사용자 + AI 메시지
        }
      } else {
        // 에러 발생 시 임시 메시지 제거
        setMessages(prev => prev.filter(msg => msg.id !== tempUserId));
        const errorMessage = getErrorMessage(parsed.errorCode);
        setError(errorMessage);
      }
    } catch (error: any) {
      // 에러 발생 시 임시 메시지 제거
      setMessages(prev => prev.filter(msg => msg.id !== tempUserId));
      
      if (error.code === 'ECONNABORTED') {
        setError('요청 시간이 초과되었습니다. 다시 시도해주세요.');
      } else {
        setError('메시지 전송에 실패했습니다.');
      }
      console.error("[useChat] sendMessage 에러:", error);
    } finally {
      setIsLoading(false);
    }
  }, [currentRoomId, selected_persona, generateUniqueId]);

  // 채팅방 생성 (사용자 액션 기반)
  const createRoom = useCallback(async (ai_persona: string, title: string) => {
    console.log("[useChat] createRoom 호출됨:", { ai_persona, title });
    try {
      const res = await apiClient.post("/api/chat/room/create", { title, ai_persona });
      console.log("[useChat] apiCreateChatRoom 응답:", res);
      const data = res as any;
      
      // 응답 구조 디버깅
      console.log("[useChat] 응답 전체 구조:", data);
      console.log("[useChat] data.room:", data.room);
      console.log("[useChat] data.data?.room:", data.data?.room);
      
      // 백엔드 응답 구조에 맞게 수정
      const newRoom = data.room || data.data?.room;
      if (newRoom) {
        console.log("[useChat] 새 채팅방 생성됨:", newRoom);
        setRooms(prev => {
          const updatedRooms = [newRoom, ...prev];
          console.log("[useChat] rooms 상태 업데이트:", { prev: prev.length, updated: updatedRooms.length });
          return updatedRooms;
        });
        setCurrentRoomId(newRoom.room_id);
        console.log("[useChat] currentRoomId 설정됨:", newRoom.room_id);
        await loadMessages(newRoom.room_id);
      } else {
        console.error("[useChat] 응답에 room 데이터가 없음:", data);
        console.error("[useChat] 응답 구조:", JSON.stringify(data, null, 2));
      }
    } catch (e) {
      setError("채팅방 생성 실패");
      console.error("채팅방 생성 실패:", e);
    }
  }, [loadMessages]);

  // 채팅방 삭제 (사용자 액션 기반)
  const deleteRoom = useCallback(async (roomId: string) => {
    try {
      await apiClient.post(`/api/chat/room/delete`, {
        room_id: roomId
      });
      setRooms(prev => prev.filter(room => room.room_id !== roomId));
      if (currentRoomId === roomId) setCurrentRoomId(null);
      // 삭제 후 즉시 목록 새로고침
      loadRooms();
    } catch (e) {
      setError("채팅방 삭제 실패");
    }
  }, [currentRoomId, loadRooms]);

  // 채팅방 이름 변경 (사용자 액션 기반)
  const handleRenameRoom = useCallback(async (roomId: string, newTitle: string) => {
    try {
      await apiClient.post(`/api/chat/room/update`, { 
        room_id: roomId, 
        new_title: newTitle 
      });
      setRooms(prev => prev.map(room => 
        room.room_id === roomId ? { ...room, title: newTitle } : room
      ));
    } catch (e) {
      setError("채팅방 이름 변경 실패");
    }
  }, []);

  return {
    rooms,
    currentRoomId,
    messages,
    isLoading,
    error,
    selected_persona,
    personas,
    typingMessageId,
    setCurrentRoomId,
    setSelected_persona,
    loadRooms,
    createRoom,
    sendMessage,
    deleteRoom,
    handleRenameRoom,
    loadMessages,
    clearError
  };
}
