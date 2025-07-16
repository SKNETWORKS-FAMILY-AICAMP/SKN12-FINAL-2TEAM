"use client"

import { useAppDispatch, useAppSelector } from "@/lib/store/hooks"
import { sendMessage, setSelectedTool, createConversation } from "@/lib/store/slices/chat-slice"

export function useChat() {
  const dispatch = useAppDispatch()
  const { conversations, currentConversationId, availableTools, selectedTool, isLoading, isStreaming, error } =
    useAppSelector((state) => state.chat)

  const currentConversation = conversations.find((c) => c.id === currentConversationId)
  const messages = currentConversation?.messages || []

  const sendChatMessage = async (content: string, tool?: string) => {
    await dispatch(sendMessage({ content, tool }))
  }

  const selectTool = (toolId: string | null) => {
    dispatch(setSelectedTool(toolId))
  }

  const createNewConversation = async (title: string) => {
    await dispatch(createConversation(title))
  }

  return {
    conversations,
    currentConversation,
    messages,
    availableTools,
    selectedTool,
    isLoading,
    isStreaming,
    error,
    sendMessage: sendChatMessage,
    selectTool,
    createConversation: createNewConversation,
  }
}
