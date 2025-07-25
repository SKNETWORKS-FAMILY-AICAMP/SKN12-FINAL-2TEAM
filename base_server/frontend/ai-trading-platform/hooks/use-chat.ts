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

  // 채팅방 목록 불러오기
  const loadRooms = useCallback(async () => {
    try {
      const res = await fetchChatRooms();
      const data = typeof res === "string" ? JSON.parse(res) : res;
      console.log("[FRONT] 채팅방 목록 응답:", data);
      const rooms = data.rooms || [];
      setRooms(rooms);
      if (rooms.length > 0) {
        setCurrentRoomId(rooms[0].room_id);
      }
    } catch (e) {
      setError("채팅방 목록 불러오기 실패");
      console.error("채팅방 목록 불러오기 실패:", e);
    }
  }, []);

  // 메시지 목록 불러오기
  const loadMessages = useCallback(async (roomId: string) => {
    try {
      const res = await fetchChatMessages(roomId);
      const data = typeof res === "string" ? JSON.parse(res) : res;
      console.log("[FRONT] 메시지 목록 응답:", data);
      setMessages((res as any).messages || []);
    } catch (e) {
      setError("메시지 불러오기 실패");
      console.error("메시지 불러오기 실패:", e);
    }
  }, []);

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
    const roomIdToUse = currentRoomId || "test_room";
    const persona = personaOverride || selectedPersona || "GPT4O";
    setIsLoading(true);
    setMessages(prev => [
      ...prev,
      { id: Date.now().toString(), content, role: "user" }
    ]);
    try {
      let res = await apiSendChatMessage(roomIdToUse, content, persona);
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
        setMessages(prev => [
          ...prev,
          {
            id: messageObj.message_id || `ai_${Date.now()}`,
            content: messageObj.content,
            role: messageObj.role || "assistant"
          }
        ]);
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
      await loadRooms();
    } catch (e) {
      setError("채팅방 삭제 실패");
    }
  }, [loadRooms]);

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
    selectedPersona,
    setSelectedPersona,
    personas,
  };
}
