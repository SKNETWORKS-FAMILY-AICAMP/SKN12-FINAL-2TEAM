"use client"

import type React from "react"

import { useState, useRef, useEffect } from "react"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { ScrollArea } from "@/components/ui/scroll-area"
import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Send, Paperclip, Mic } from "lucide-react"
import ChatMessage from "./chat-message"
import { TypingIndicator } from "./typing-indicator"
import { useChat } from "@/hooks/use-chat"

interface ChatInterfaceProps {
  selectedTool: string | null
}

export function ChatInterface({ selectedTool }: ChatInterfaceProps) {
  const [message, setMessage] = useState("")
  const { messages, sendMessage, isLoading } = useChat()
  const scrollAreaRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (scrollAreaRef.current) {
      scrollAreaRef.current.scrollTop = scrollAreaRef.current.scrollHeight
    }
  }, [messages])

  const handleSend = async () => {
    if (!message.trim()) return

    await sendMessage(message, selectedTool ?? undefined)
    setMessage("")
  }

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="flex flex-col h-full">
      {/* Messages Area */}
      <ScrollArea className="flex-1 p-4" ref={scrollAreaRef}>
        <div className="space-y-4">
          {messages.length === 0 && (
            <div className="text-center py-12">
              <div className="w-16 h-16 bg-blue-100 dark:bg-blue-900/20 rounded-full flex items-center justify-center mx-auto mb-4">
                <Avatar className="w-12 h-12">
                  <AvatarImage src="/ai-avatar.png" />
                  <AvatarFallback>AI</AvatarFallback>
                </Avatar>
              </div>
              <h3 className="text-lg font-medium mb-2">AI 트레이딩 어드바이저에게 물어보세요</h3>
              <p className="text-gray-600 dark:text-gray-400 text-sm">
                시장 분석, 투자 전략, 포트폴리오 관리 등 무엇이든 도움드릴게요
              </p>
            </div>
          )}

          {messages.map((msg) => (
            <ChatMessage key={msg.id} message={msg} />
          ))}

          {isLoading && <TypingIndicator />}
        </div>
      </ScrollArea>

      {/* Input Area */}
      <div className="border-t p-4">
        <div className="flex items-end gap-2">
          <div className="flex-1">
            <Input
              value={message}
              onChange={(e) => setMessage(e.target.value)}
              onKeyPress={handleKeyPress}
              placeholder="메시지를 입력하세요..."
              className="min-h-[44px] resize-none"
              disabled={isLoading}
            />
          </div>
          <div className="flex gap-1">
            <Button size="icon" variant="outline">
              <Paperclip className="h-4 w-4" />
            </Button>
            <Button size="icon" variant="outline">
              <Mic className="h-4 w-4" />
            </Button>
            <Button size="icon" onClick={handleSend} disabled={!message.trim() || isLoading}>
              <Send className="h-4 w-4" />
            </Button>
          </div>
        </div>

        {selectedTool && <div className="mt-2 text-xs text-gray-500">활성 도구: {selectedTool}</div>}
      </div>
    </div>
  )
}
