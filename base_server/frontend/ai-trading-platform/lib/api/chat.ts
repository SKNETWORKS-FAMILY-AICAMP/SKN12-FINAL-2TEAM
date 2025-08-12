import axios from "axios";
import { apiClient } from "./client";

// 채팅방 목록 요청
export async function fetchChatRooms(page = 1, limit = 20) {
  // chat_serialize.py의 ChatRoomListRequest와 일치
  const payload = { page, limit };
  console.log("[FRONT] 채팅방 목록 요청 payload:", payload);
  const res = await apiClient.post("/api/chat/rooms", payload);
  console.log("[FRONT] 채팅방 목록 응답:", res);
  return res;
}

// 새 채팅방 생성
export async function createChatRoom(title: string, ai_persona: string = "GPT4O") {
  const payload = { title, ai_persona };
  console.log("[FRONT] 채팅방 생성 요청 payload:", payload);
  const res = await apiClient.post("/api/chat/room/create", payload);
  console.log("[FRONT] 채팅방 생성 응답:", res);
  return res;
}

// 메시지 전송
export async function sendMessage(roomId: string, message: string, messageType: string = "TEXT") {
  const accessToken = typeof window !== "undefined" ? localStorage.getItem("accessToken") : "";
  const sequence = Date.now();
  
  const payload = { 
    room_id: roomId, 
    content: message, 
    include_portfolio: true,
    analysis_symbols: [],
    ai_persona: "GPT4O",  // 백엔드 모델에 필수인 ai_persona 필드 추가
    accessToken: accessToken,
    sequence: sequence
  };
  console.log("[FRONT] 메시지 전송 요청 payload:", payload);
  console.log("[FRONT] localStorage accessToken:", typeof window !== "undefined" ? localStorage.getItem("accessToken") : "N/A");
  
  const res = await apiClient.post("/api/chat/message/send", payload);
  console.log("[FRONT] 메시지 전송 응답:", res);
  return res;
}

// 메시지 목록 조회
export async function fetchMessages(roomId: string, page = 1, limit = 50) {
  const payload = { room_id: roomId, page, limit };
  console.log("[FRONT] 메시지 목록 요청 payload:", payload);
  const res = await apiClient.post("/api/chat/messages", payload);
  console.log("[FRONT] 메시지 목록 응답:", res);
  return res;
}

// 채팅방 제목 업데이트
export async function updateChatRoomTitle(roomId: string, title: string) {
  return await apiClient.post("/api/chat/room/update", {
    room_id: roomId,
    new_title: title
  });
}

// 채팅방 삭제
export async function deleteChatRoom(roomId: string) {
  return await apiClient.post("/api/chat/room/delete", {
    room_id: roomId
  });
}