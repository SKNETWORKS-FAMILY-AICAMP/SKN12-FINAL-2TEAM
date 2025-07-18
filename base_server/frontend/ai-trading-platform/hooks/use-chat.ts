"use client"

import { useState, useCallback, useEffect } from "react"
import { authManager } from "@/lib/auth"
import { createChatRoom, sendChatMessage, getChatMessages, getPersonaList } from "@/lib/api/chat"

export function useChat() {
  const [rooms, setRooms] = useState<Array<{ room_id: string; room_name: string; ai_persona: string }>>([])
  const [currentRoomId, setCurrentRoomId] = useState<string | null>(null)
  const [messages, setMessages] = useState<Array<{ sender: string; message: string; sent_at: string }>>([])
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [personas, setPersonas] = useState<Array<{ persona_id: string; name: string; description: string; avatar_url: string }>>([])
  const [selectedPersona, setSelectedPersona] = useState<string | null>(null)

  // Fetch persona list on mount
  useEffect(() => {
    const fetchPersonas = async () => {
      try {
        const token = authManager.getToken()
        if (!token) return
        const res = await getPersonaList(token)
        const list = res.data?.personas?.slice(0, 3) || []
        setPersonas(list)
        if (list.length > 0) setSelectedPersona(list[0].persona_id)
      } catch (e) {
        // ignore
      }
    }
    fetchPersonas()
  }, [])

  // Fetch messages when currentRoomId changes
  useEffect(() => {
    const fetchMessages = async () => {
      if (!currentRoomId) return
      setIsLoading(true)
      setError(null)
      try {
        const token = authManager.getToken()
        if (!token) throw new Error("로그인이 필요합니다.")
        const res = await getChatMessages(token, currentRoomId)
        setMessages(
          (res.data?.messages || []).map((m: any) => ({
            sender: m.sender,
            message: m.message,
            sent_at: m.sent_at,
          }))
        )
      } catch (e: any) {
        setError(e.message || "메시지 불러오기 실패")
      } finally {
        setIsLoading(false)
      }
    }
    fetchMessages()
  }, [currentRoomId])

  // Create a new chat room (with persona)
  const createRoom = useCallback(async (roomName: string, aiPersona?: string) => {
    setIsLoading(true)
    setError(null)
    try {
      const token = authManager.getToken()
      if (!token) throw new Error("로그인이 필요합니다.")
      const persona = aiPersona || selectedPersona || (personas[0]?.persona_id ?? "GPT4O")
      const res = await createChatRoom(token, roomName, persona)
      const room = {
        room_id: res.data.room_id,
        room_name: res.data.room_name,
        ai_persona: res.data.ai_persona,
      }
      setRooms((prev) => [room, ...prev])
      setCurrentRoomId(room.room_id)
      setMessages([])
    } catch (e: any) {
      setError(e.message || "채팅방 생성 실패")
    } finally {
      setIsLoading(false)
    }
  }, [selectedPersona, personas])

  // Send a message in the current room
  const sendMessage = useCallback(async (message: string) => {
    if (!currentRoomId) return
    setIsLoading(true)
    setError(null)
    try {
      const token = authManager.getToken()
      if (!token) throw new Error("로그인이 필요합니다.")
      const res = await sendChatMessage(token, currentRoomId, message)
      // Append user message and AI response
      setMessages((prev) => [
        ...prev,
        { sender: "user", message, sent_at: new Date().toISOString() },
        { sender: "ai", message: res.data.ai_response.message, sent_at: res.data.ai_response.sent_at },
      ])
    } catch (e: any) {
      setError(e.message || "메시지 전송 실패")
    } finally {
      setIsLoading(false)
    }
  }, [currentRoomId])

  return {
    rooms,
    currentRoomId,
    setCurrentRoomId,
    messages,
    isLoading,
    error,
    createRoom,
    sendMessage,
    personas,
    selectedPersona,
    setSelectedPersona,
  }
}
