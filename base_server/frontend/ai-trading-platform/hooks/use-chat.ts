"use client"

import { useState, useCallback, useEffect } from "react";
import {
  fetchChatRooms,
  createChatRoom as apiCreateChatRoom,
  sendChatMessage as apiSendChatMessage,
  fetchChatMessages,
  deleteChatRoom as apiDeleteChatRoom
} from "@/lib/api/chat";

interface LocalMessage {
  id: string;
  content: string;
  role: string;
}

export function useChat() {
  const [rooms, setRooms] = useState<any[]>([]);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [currentRoomId, setCurrentRoomId] = useState<string | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<string>("GPT4O");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [personas, setPersonas] = useState<any[]>([]);
  const [messageCache, setMessageCache] = useState<Record<string, LocalMessage[]>>({}); // 채팅방별 메시지 캐시
  const [isInitialLoad, setIsInitialLoad] = useState(true); // 초기 로드 여부

  // 채팅방 목록 불러오기
  const loadRooms = useCallback(async () => {
    try {
      const res = await fetchChatRooms();
      const data = typeof res === "string" ? JSON.parse(res) : res;
      console.log("[FRONT] 채팅방 목록 응답:", data);
      const rooms = data.rooms || [];
      setRooms(rooms);
      // 초기 로드 시에만 자동으로 첫 번째 방 선택
      if (isInitialLoad && rooms.length > 0 && !currentRoomId) {
        setCurrentRoomId(rooms[0].room_id);
        setIsInitialLoad(false);
      }
    } catch (e) {
      setError("채팅방 목록 불러오기 실패");
      console.error("채팅방 목록 불러오기 실패:", e);
    }
  }, [currentRoomId]);

  // 메시지 목록 불러오기
  const loadMessages = useCallback(async (roomId: string) => {
    try {
      console.log("[FRONT] 메시지 로드 시작 - room_id:", roomId);
      const res = await fetchChatMessages(roomId);
      const data = typeof res === "string" ? JSON.parse(res) : res;
      console.log("[FRONT] 메시지 목록 응답:", data);
      
      // 응답 구조 확인 및 메시지 추출
      let messages = [];
      if (data && data.messages) {
        messages = data.messages;
      } else if (data && data.data && data.data.messages) {
        messages = data.data.messages;
      }
      
      console.log("[FRONT] 추출된 메시지:", messages);
      console.log("[FRONT] 메시지 상세 정보:");
      messages.forEach((msg: any, index: number) => {
        console.log(`[FRONT] 메시지 ${index}:`, {
          message_id: msg.message_id,
          message_type: msg.message_type,
          sender_type: msg.sender_type,
          content: msg.content?.substring(0, 50) + "...",
          role: msg.role
        });
      });
      
      // 메시지를 LocalMessage 형식으로 변환
      const localMessages: LocalMessage[] = messages.map((msg: any) => {
        console.log("[FRONT] 메시지 변환:", msg);
        let role = "assistant"; // 기본값
        
        // 다양한 메시지 타입 필드 확인
        if (msg.message_type === "USER" || msg.sender_type === "USER") {
          role = "user";
        } else if (msg.message_type === "AI" || msg.sender_type === "AI") {
          role = "assistant";
        } else if (msg.role) {
          // 이미 role 필드가 있는 경우
          role = msg.role;
        }
        
        return {
          id: msg.message_id || msg.id || `msg_${Date.now()}`,
          content: msg.content || "",
          role: role
        };
      });
      
      // 캐시에 저장
      setMessageCache(prev => ({
        ...prev,
        [roomId]: localMessages
      }));
      
      // 현재 채팅방이면 메시지 상태 업데이트
      if (currentRoomId === roomId) {
        setMessages(localMessages);
      }
      
      console.log("[FRONT] 메시지 로드 완료 - room_id:", roomId, "개수:", localMessages.length);
    } catch (e) {
      setError("메시지 불러오기 실패");
      console.error("메시지 불러오기 실패:", e);
    }
  }, [currentRoomId]);

  // 채팅방 생성
  const createRoom = useCallback(async (aiPersona: string, title = "") => {
    try {
      const res = await apiCreateChatRoom(aiPersona, title);
      const data = typeof res === "string" ? JSON.parse(res) : res;
      console.log("[FRONT] 채팅방 생성 응답:", data);
      // errorCode가 0이면 optimistic update
      if (data && data.errorCode === 0 && data.room) {
        setRooms(prev => [data.room, ...prev]);
        setCurrentRoomId(data.room.room_id);
        await loadMessages(data.room.room_id); // 새 방 생성 후 바로 메시지 목록 불러오기
      } else {
        await loadRooms(); // fallback
      }
    } catch (e) {
      setError("채팅방 생성 실패");
      console.error("채팅방 생성 실패:", e);
    }
  }, [loadRooms, loadMessages]);

  // 메시지 전송
  const sendMessage = useCallback(async (content: string, personaOverride?: string) => {
    const persona = personaOverride || selectedPersona || "GPT4O";
    
    // 채팅방이 없으면 메시지 전송 불가
    if (!currentRoomId) {
      setError("채팅방을 먼저 선택하거나 새 채팅방을 생성해주세요.");
      return;
    }
    
    setIsLoading(true);
    
    // 사용자 메시지를 즉시 추가
    const userMessage: LocalMessage = { 
      id: Date.now().toString(), 
      content, 
      role: "user" 
    };
    
    setMessages(prev => [...prev, userMessage]);
    
    try {
      console.log("[FRONT] 메시지 전송 - room_id:", currentRoomId);
      let res = await apiSendChatMessage(currentRoomId, content, persona);
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
        const aiMessage: LocalMessage = {
          id: messageObj.message_id || `ai_${Date.now()}`,
          content: messageObj.content,
          role: "assistant"
        };
        
        // 현재 메시지 상태 업데이트
        setMessages(prev => [...prev, aiMessage]);
        
        // 캐시 업데이트
        setMessageCache(prev => ({
          ...prev,
          [currentRoomId]: [...(prev[currentRoomId] || []), userMessage, aiMessage]
        }));
      }
    } catch (e) {
      setError("메시지 전송 실패");
      console.error("메시지 전송 실패:", e);
    } finally {
      setIsLoading(false);
    }
  }, [currentRoomId, selectedPersona, apiCreateChatRoom]);

  // 채팅방 삭제
  const deleteRoom = useCallback(async (roomId: string) => {
    try {
      await apiDeleteChatRoom(roomId);
      
      // 삭제된 채팅방의 캐시도 정리
      setMessageCache(prev => {
        const newCache = { ...prev };
        delete newCache[roomId];
        return newCache;
      });
      
      // 현재 선택된 채팅방이 삭제된 방이면 선택 해제
      if (currentRoomId === roomId) {
        setCurrentRoomId(null);
        setMessages([]);
        setIsInitialLoad(false); // 삭제 후에는 자동 선택 비활성화
      }
      
      await loadRooms();
    } catch (e) {
      setError("채팅방 삭제 실패");
    }
  }, [loadRooms, currentRoomId]);

  useEffect(() => {
    if (isInitialLoad) {
      loadRooms();
    }
  }, [loadRooms, isInitialLoad]);

  useEffect(() => {
    if (currentRoomId) {
      console.log("[FRONT] 채팅방 변경:", currentRoomId);
      
      // 캐시된 메시지가 있으면 먼저 사용
      if (messageCache[currentRoomId]) {
        console.log("[FRONT] 캐시된 메시지 사용:", messageCache[currentRoomId].length, "개");
        setMessages(messageCache[currentRoomId]);
      } else {
        console.log("[FRONT] 캐시된 메시지 없음, DB에서 로드");
        setMessages([]); // 로딩 중 빈 배열로 초기화
        loadMessages(currentRoomId);
      }
    }
  }, [currentRoomId, messageCache, loadMessages]);

  useEffect(() => {
    setPersonas([
      { persona_id: "market_analysis", name: "시장 분석" },
      { persona_id: "stock_screener", name: "종목 스크리너" },
      { persona_id: "portfolio_optimizer", name: "포트폴리오 최적화" },
      { persona_id: "trading_signals", name: "트레이딩 시그널" },
    ]);
  }, []);

  return {
    rooms,
    currentRoomId,
    setCurrentRoomId,
    messages,
    isLoading,
    error,
    createRoom,
    sendMessage,
    deleteRoom,
    selectedPersona,
    setSelectedPersona,
    personas,
  };
}
