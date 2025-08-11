"use client"

import { useState, useCallback, useEffect, useRef } from "react"
import { apiClient } from "@/lib/api/client"
import { handleApiError, getErrorMessage } from "@/lib/error-handler"

interface LocalMessage {
  id: string;
  content: string;
  role: string;
  isTyping?: boolean;
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
      
      if (response.errorCode === 0) {
        setMessages(response.messages || [])
      } else {
        const errorMessage = getErrorMessage(response.errorCode)
        setError(errorMessage)
      }
    } catch (e: any) {
      const errorInfo = handleApiError(e)
      
      if (errorInfo.isSessionExpired) {
        setError("세션이 만료되어 로그인 페이지로 이동합니다.")
        return
      }
      
      setError(errorInfo.message)
      console.error("메시지 목록 불러오기 실패:", e)
    } finally {
      setIsLoading(false)
    }
  }, [])

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
    const persona = personaOverride || selected_persona || "GPT4O";
    setIsLoading(true);
    
    // 고유한 ID 생성 (타임스탬프 + 랜덤 값 + 인덱스)
    const uniqueId = `user_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${messages.length}`;
    
    setMessages(prev => [
      ...prev,
      { id: uniqueId, content, role: "user" }
    ]);
    try {
      let res = await apiClient.post(`/api/chat/message/send`, { room_id: roomIdToUse, content, ai_persona: persona });
      let parsed: any = res;
      if (parsed && parsed.data && typeof parsed.data === "object") {
        parsed = parsed.data;
      } else if (parsed && parsed.data && typeof parsed.data === "string") {
        try {
          parsed = JSON.parse(parsed.data);
        } catch (err) {
          console.error("응답 data 파싱 실패:", err);
          setError("메시지 전송 실패");
          return;
        }
      } else if (typeof parsed === "string") {
        try {
          parsed = JSON.parse(parsed);
        } catch (err) {
          console.error("응답 전체 파싱 실패:", err);
          setError("메시지 전송 실패");
          return;
        }
      }
      const messageObj = parsed.message;
      if (messageObj && messageObj.content) {
        const aiMessageId = messageObj.message_id || `ai_${Date.now()}_${Math.random().toString(36).substr(2, 9)}_${messages.length}`;
        
        // 타이핑 효과를 위한 AI 메시지 추가
        const typingMessage: LocalMessage = {
          id: aiMessageId,
          content: messageObj.content,
          role: "assistant",
          isTyping: true
        };
        
        setTypingMessageId(aiMessageId);
        setMessages(prev => [...prev, typingMessage]);
        
        // 타이핑 완료 후 실제 메시지로 변경
        setTimeout(() => {
          const finalMessage: LocalMessage = {
            id: aiMessageId,
            content: messageObj.content,
            role: "assistant"
          };
          
          setMessages(prev => prev.map(msg => 
            msg.id === aiMessageId ? finalMessage : msg
          ));
          
          setTypingMessageId(null);
        }, (messageObj.content.split(/\n\s*\n/).filter((p: string) => p.trim().length > 0).length * 400) + 300); // 문단 수에 비례한 지연
      }
    } catch (e) {
      setError("메시지 전송 실패");
    } finally {
      setIsLoading(false);
    }
  }, [currentRoomId, selected_persona]);

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
