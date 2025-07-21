import axios from "axios";

// 채팅방 목록 요청
export async function fetchChatRooms(accessToken: string, page = 1, limit = 20) {
  return axios.post("/api/chat/rooms", { accessToken, page, limit });
}

// 채팅방 생성
export async function createChatRoom(accessToken: string, ai_persona: string, title = "") {
  return axios.post("/api/chat/room/create", { accessToken, ai_persona, title });
}

// 메시지 전송 (ChatMessageSendRequest 형식에 맞게)
export async function sendChatMessage(accessToken: string, room_id: string, content: string, persona: string) {
  return axios.post("/api/chat/message/send", {
    accessToken, // BaseRequest에서 상속받으므로 반드시 포함
    room_id,
    content,
    persona
  });
}

// 메시지 목록
export async function fetchChatMessages(accessToken: string, room_id: string, page = 1, limit = 50, before_timestamp = "") {
  return axios.post("/api/chat/messages", { accessToken, room_id, page, limit, before_timestamp });
}

// 채팅방 삭제
export async function deleteChatRoom(accessToken: string, room_id: string) {
  return axios.post("/api/chat/room/delete", { accessToken, room_id });
} 