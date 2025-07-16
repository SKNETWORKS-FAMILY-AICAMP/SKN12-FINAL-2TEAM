"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Bot, User, Clock } from "lucide-react"

interface ChatMessage {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: number
  metadata?: {
    tool?: string
    confidence?: number
    sources?: string[]
  }
}

interface ChatMessageProps {
  message: ChatMessage
}

export function ChatMessage({ message }: ChatMessageProps) {
  const isUser = message.role === "user"
  const formattedTime = new Date(message.timestamp).toLocaleTimeString("ko-KR", {
    hour: "2-digit",
    minute: "2-digit",
  })

  return (
    <div className={`flex gap-3 ${isUser ? "flex-row-reverse" : "flex-row"}`}>
      <Avatar className="w-8 h-8 flex-shrink-0">
        {isUser ? (
          <>
            <AvatarImage src="/avatars/user.jpg" />
            <AvatarFallback className="bg-blue-500 text-white">
              <User className="h-4 w-4" />
            </AvatarFallback>
          </>
        ) : (
          <>
            <AvatarImage src="/avatars/ai.jpg" />
            <AvatarFallback className="bg-gradient-to-br from-purple-500 to-pink-600 text-white">
              <Bot className="h-4 w-4" />
            </AvatarFallback>
          </>
        )}
      </Avatar>

      <div className={`flex-1 max-w-[80%] ${isUser ? "text-right" : "text-left"}`}>
        <Card
          className={`${
            isUser
              ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white border-0"
              : "bg-white dark:bg-slate-800 border border-gray-200 dark:border-gray-700"
          }`}
        >
          <CardContent className="p-4">
            <div className="space-y-2">
              <p className="text-sm leading-relaxed whitespace-pre-wrap">{message.content}</p>

              {message.metadata && (
                <div className="flex flex-wrap gap-2 mt-3">
                  {message.metadata.tool && (
                    <Badge variant="outline" className={`text-xs ${isUser ? "border-white/30 text-white" : ""}`}>
                      도구: {message.metadata.tool}
                    </Badge>
                  )}
                  {message.metadata.confidence && (
                    <Badge variant="outline" className={`text-xs ${isUser ? "border-white/30 text-white" : ""}`}>
                      신뢰도: {message.metadata.confidence}%
                    </Badge>
                  )}
                </div>
              )}

              {message.metadata?.sources && (
                <div className="mt-3 pt-2 border-t border-gray-200 dark:border-gray-600">
                  <p className="text-xs text-gray-500 dark:text-gray-400 mb-1">참고 자료:</p>
                  <div className="flex flex-wrap gap-1">
                    {message.metadata.sources.map((source, index) => (
                      <Badge key={index} variant="secondary" className="text-xs">
                        {source}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        <div
          className={`flex items-center gap-1 mt-1 text-xs text-gray-500 ${isUser ? "justify-end" : "justify-start"}`}
        >
          <Clock className="h-3 w-3" />
          <span>{formattedTime}</span>
        </div>
      </div>
    </div>
  )
}
