// 실제 서비스용 Chat API 클라이언트

const BASE_URL = "http://localhost:8000";

export async function createChatRoom(accessToken: string, roomName: string, aiPersona: string) {
  const res = await fetch(`${BASE_URL}/api/chat/room/create`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_token: accessToken, room_name: roomName, ai_persona: aiPersona }),
  });
  if (!res.ok) throw new Error("Failed to create chat room");
  return res.json();
}

export async function sendChatMessage(accessToken: string, roomId: string, message: string) {
  const res = await fetch(`${BASE_URL}/api/chat/message/send`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_token: accessToken, room_id: roomId, message, message_type: "text" }),
  });
  if (!res.ok) throw new Error("Failed to send chat message");
  return res.json();
}

export async function getChatMessages(accessToken: string, roomId: string, limit = 50) {
  const res = await fetch(`${BASE_URL}/api/chat/messages`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_token: accessToken, room_id: roomId, limit }),
  });
  if (!res.ok) throw new Error("Failed to fetch chat messages");
  return res.json();
}

export async function getPersonaList(accessToken: string) {
  const res = await fetch(`${BASE_URL}/api/chat/personas`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ access_token: accessToken }),
  });
  if (!res.ok) throw new Error("Failed to fetch persona list");
  return res.json();
} 