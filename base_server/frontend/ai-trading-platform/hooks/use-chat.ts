"use client"

import { useState, useCallback, useEffect } from "react";
import {
  fetchChatRooms,
  createChatRoom as apiCreateChatRoom,
  sendMessage as apiSendChatMessage,
  fetchMessages,
  deleteChatRoom as apiDeleteChatRoom,
  updateChatRoomTitle as apiUpdateChatRoomTitle
} from "@/lib/api/chat";

interface LocalMessage {
  id: string;
  content: string;
  role: string;
  isTyping?: boolean;
}

export function useChat() {
  const [rooms, setRooms] = useState<any[]>([]);
  const [messages, setMessages] = useState<LocalMessage[]>([]);
  const [currentRoomId, setCurrentRoomId] = useState<string | null>(null);
  const [selectedPersona, setSelectedPersona] = useState<string>("GPT4O");
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [personas, setPersonas] = useState<any[]>([]);
  const [typingMessageId, setTypingMessageId] = useState<string | null>(null);

  // 채팅방 목록 불러오기 (항상 백엔드에서 최신 데이터 사용)
  const loadRooms = useCallback(async () => {
    try {
      const res = await fetchChatRooms();
      const data = typeof res === "string" ? JSON.parse(res) : res;
      let rooms = data.rooms || [];
      // room_state가 'DELETED'이거나, 방 정보가 불완전하면 무조건 목록에서 제외
      rooms = rooms.filter((room: any) => {
        if (!room) return false;
        if (room.room_state === 'DELETED') return false;
        if (!room.room_id || !room.title || !room.ai_persona) return false;
        return true;
      });
      setRooms(rooms);
      if (rooms.length === 0) setCurrentRoomId(null);
      else if (!rooms.find((r: any) => r.room_id === currentRoomId)) setCurrentRoomId(rooms[0].room_id);
    } catch (e) {
      setError("채팅방 목록 불러오기 실패");
    }
  }, [currentRoomId]);

  // 메시지 목록 불러오기
  const loadMessages = useCallback(async (roomId: string) => {
    try {
      const res = await fetchMessages(roomId);
      const data = typeof res === "string" ? JSON.parse(res) : res;
      console.log("[FRONT] 메시지 목록 응답:", data);
      // sender_type을 role로 변환
      const rawMessages =
        (data && data.messages) ||
        (data && data.data && data.data.messages) ||
        [];
      const mappedMessages = rawMessages.map((msg: any) => ({
        id: msg.id || msg.message_id,
        content: msg.content,
        role: msg.role || (msg.sender_type === 'USER' ? 'user' : 'assistant'),
        isTyping: msg.isTyping,
      }));
      setMessages(mappedMessages);
    } catch (e) {
      setError("메시지 불러오기 실패");
      console.error("메시지 불러오기 실패:", e);
    }
  }, []);

  // 채팅방 생성
  const createRoom = useCallback(async (aiPersona: string, title = "") => {
    try {
      const res = await apiCreateChatRoom(title, aiPersona);
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
    const roomIdToUse = currentRoomId || "test_room";
    const persona = personaOverride || selectedPersona || "GPT4O";
    setIsLoading(true);
    setMessages(prev => [
      ...prev,
      { id: Date.now().toString(), content, role: "user" }
    ]);
    try {
      let res = await apiSendChatMessage(roomIdToUse, content);
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
        const aiMessageId = messageObj.message_id || `ai_${Date.now()}`;
        
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
  }, [currentRoomId, selectedPersona]);

  // 채팅방 삭제
  const deleteRoom = useCallback(async (roomId: string) => {
    try {
      await apiDeleteChatRoom(roomId);
      setRooms(prev => prev.filter(room => room.room_id !== roomId));
      if (currentRoomId === roomId) setCurrentRoomId(null);
      // 삭제 후 즉시 목록 새로고침
      loadRooms();
    } catch (e) {
      setError("채팅방 삭제 실패");
    }
  }, [currentRoomId, loadRooms]);

  // 채팅방 이름 변경
  const handleRenameRoom = useCallback(async (roomId: string, newTitle: string) => {
    try {
      await apiUpdateChatRoomTitle(roomId, newTitle);
      setRooms(prev =>
        prev.map(room =>
          room.room_id === roomId ? { ...room, title: newTitle } : room
        )
      );
    } catch (e) {
      setError("채팅방 이름 변경 실패");
    }
  }, []);

  useEffect(() => {
    loadRooms();
  }, [loadRooms]);

  useEffect(() => {
    if (currentRoomId) {
      loadMessages(currentRoomId);
    }
  }, [currentRoomId, loadMessages]);

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
    handleRenameRoom, // 추가
    selectedPersona,
    setSelectedPersona,
    personas,
  };
}
