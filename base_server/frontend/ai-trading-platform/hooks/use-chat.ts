"use client"

import { useState, useCallback, useEffect } from "react"
import { authManager } from "@/lib/auth"
import { useAppDispatch, useAppSelector } from "@/lib/store/hooks"
import { sendMessage as sendMessageAction, createConversation, setCurrentConversation } from "@/lib/store/slices/chat-slice"

export function useChat() {
  const dispatch = useAppDispatch()
  const { conversations, currentConversationId, availableTools, isLoading, error } = useAppSelector((state) => state.chat)
  
  const currentConversation = conversations.find(c => c.id === currentConversationId)
  const messages = currentConversation?.messages || []

  // Fetch persona list on mount - 현재는 Redux store에서 관리하므로 불필요
  useEffect(() => {
    // Redux store에서 이미 availableTools로 관리됨
  }, [])

  // Fetch messages when currentConversationId changes - Redux store에서 관리됨
  useEffect(() => {
    // Redux store에서 이미 메시지가 관리되므로 불필요
  }, [currentConversationId])

  // Create a new chat room (with persona)
  const createRoom = useCallback(async (roomName: string, aiPersona?: string) => {
    try {
      await dispatch(createConversation(roomName))
    } catch (e: any) {
      console.error("채팅방 생성 실패:", e)
    }
  }, [dispatch])

  // Send a message in the current room
  const sendMessage = useCallback(async (message: string) => {
    if (!currentConversationId) return
    try {
      await dispatch(sendMessageAction({ content: message }))
    } catch (e: any) {
      console.error("메시지 전송 실패:", e)
    }
  }, [currentConversationId, dispatch])

  return {
    rooms: conversations.map(c => ({ room_id: c.id, room_name: c.title, ai_persona: "GPT4O" })),
    currentRoomId: currentConversationId,
    setCurrentRoomId: (id: string) => dispatch(setCurrentConversation(id)),
    messages: messages.map(m => ({ sender: m.role, message: m.content, sent_at: new Date(m.timestamp).toISOString() })),
    isLoading,
    error,
    createRoom,
    sendMessage,
    personas: availableTools.map(t => ({ persona_id: t.id, name: t.name, description: t.description, avatar_url: "" })),
    selectedPersona: null,
    setSelectedPersona: () => {},
  }
}
