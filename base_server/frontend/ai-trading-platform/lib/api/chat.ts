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

// 채팅방 생성
export async function createChatRoom(ai_persona: string, title = "") {
  const accessToken = typeof window !== "undefined" ? localStorage.getItem("accessToken") : "";
  const sequence = Date.now();
  const payload = { accessToken, sequence, ai_persona, title };
  console.log("[FRONT] 채팅방 생성 요청 payload:", payload);
  console.log("[FRONT] Authorization 헤더:", accessToken ? `Bearer ${accessToken}` : "(없음)");
  const res = await apiClient.post("/api/chat/room/create", payload);
  console.log("[FRONT] 채팅방 생성 응답:", res);
  return res;
}

// 메시지 전송 (ChatMessageSendRequest 형식에 맞게)
export async function sendChatMessage(room_id: string, content: string, persona: string) {
  // chat_serialize.py의 ChatMessageSendRequest와 일치
  const payload = { room_id, content, persona };
  console.log("[FRONT] 메시지 전송 요청 payload:", payload);
  console.log("[FRONT] room_id 타입:", typeof room_id, "값:", room_id);
  console.log("[FRONT] content 타입:", typeof content, "값:", content);
  console.log("[FRONT] persona 타입:", typeof persona, "값:", persona);
  const res = await apiClient.post("/api/chat/message/send", payload);
  console.log("[FRONT] 메시지 전송 응답:", res);
  return res;
}

// 메시지 목록
export async function fetchChatMessages(room_id: string, page = 1, limit = 50, before_timestamp = "") {
  const accessToken = typeof window !== "undefined" ? localStorage.getItem("accessToken") : "";
  const sequence = Date.now();
  const payload = { accessToken, sequence, room_id, page, limit, before_timestamp };
  console.log("[FRONT] 메시지 목록 요청 payload:", payload);
  console.log("[FRONT] room_id 타입:", typeof room_id, "값:", room_id);
  const res = await apiClient.post("/api/chat/messages", payload);
  console.log("[FRONT] 메시지 목록 응답:", res);
  console.log("[FRONT] 응답 타입:", typeof res);
  if (res && typeof res === "object" && "data" in res) {
    console.log("[FRONT] res.data:", (res as any).data);
  }
  return res;
}

// 채팅방 이름 변경
export async function updateChatRoomTitle(roomId: string, newTitle: string) {
  const accessToken = typeof window !== "undefined" ? localStorage.getItem("accessToken") || "" : "";
  const sequence = Date.now();
  return await apiClient.post("/api/chat/room/update", {
    room_id: roomId,
    new_title: newTitle,
    accessToken,
    sequence,
  });
}

// 채팅방 삭제
export async function deleteChatRoom(roomId: string) {
  return await apiClient.post("/api/chat/room/delete", {
    room_id: roomId,
  });
} 