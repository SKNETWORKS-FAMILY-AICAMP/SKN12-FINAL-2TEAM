import axios from "axios";

// 채팅방 목록 요청
export async function fetchChatRooms(accessToken: string, page = 1, limit = 20) {
  // chat_serialize.py의 ChatRoomListRequest와 일치
  const payload = { accessToken, page, limit };
  console.log("[FRONT] 채팅방 목록 요청 payload:", payload);
  const res = await axios.post("/api/chat/rooms", payload);
  console.log("[FRONT] 채팅방 목록 응답:", res.data);
  return res;
}

// 채팅방 생성
export async function createChatRoom(accessToken: string, ai_persona: string, title = "") {
  // chat_serialize.py의 ChatRoomCreateRequest와 100% 일치
  const payload = { accessToken, ai_persona, title };
  console.log("[FRONT] 채팅방 생성 요청 payload:", payload);
  const res = await axios.post("/api/chat/room/create", payload);
  console.log("[FRONT] 채팅방 생성 응답:", res.data);
  return res;
}

// 메시지 전송 (ChatMessageSendRequest 형식에 맞게)
export async function sendChatMessage(accessToken: string, room_id: string, content: string, persona: string) {
  // chat_serialize.py의 ChatMessageSendRequest와 일치
  const payload = { accessToken, room_id, content, persona };
  console.log("[FRONT] 메시지 전송 요청 payload:", payload);
  const res = await axios.post("/api/chat/message/send", payload);
  console.log("[FRONT] 메시지 전송 응답:", res.data);
  return res;
}

// 메시지 목록
export async function fetchChatMessages(accessToken: string, room_id: string, page = 1, limit = 50, before_timestamp = "") {
  // chat_serialize.py의 ChatMessageListRequest와 일치
  const payload = { accessToken, room_id, page, limit, before_timestamp };
  console.log("[FRONT] 메시지 목록 요청 payload:", payload);
  const res = await axios.post("/api/chat/messages", payload);
  console.log("[FRONT] 메시지 목록 응답:", res.data);
  return res;
}

// 채팅방 삭제
export async function deleteChatRoom(accessToken: string, room_id: string) {
  // chat_serialize.py의 ChatRoomDeleteRequest와 일치
  const payload = { accessToken, room_id };
  console.log("[FRONT] 채팅방 삭제 요청 payload:", payload);
  const res = await axios.post("/api/chat/room/delete", payload);
  console.log("[FRONT] 채팅방 삭제 응답:", res.data);
  return res;
} 