"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Plus, MessageSquare, Clock } from "lucide-react"
import { useChat } from "@/hooks/use-chat"

export function ChatSidebar() {
  const { conversations, currentConversation, createConversation } = useChat()

  const handleNewChat = () => {
    createConversation("새로운 대화")
  }

  return (
    <Card className="h-full border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
      <CardHeader className="pb-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg">대화 목록</CardTitle>
          <Button size="sm" onClick={handleNewChat} className="bg-gradient-to-r from-blue-500 to-indigo-600">
            <Plus className="h-4 w-4 mr-1" />새 대화
          </Button>
        </div>
      </CardHeader>

      <CardContent className="space-y-2">
        {conversations.map((conversation) => (
          <div
            key={conversation.id}
            className={`p-3 rounded-lg cursor-pointer transition-all duration-200 ${
              currentConversation?.id === conversation.id
                ? "bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow-md"
                : "bg-gray-50 dark:bg-slate-700/50 hover:bg-gray-100 dark:hover:bg-slate-700"
            }`}
          >
            <div className="flex items-center gap-2 mb-2">
              <MessageSquare className="h-4 w-4 flex-shrink-0" />
              <h3 className="font-medium text-sm truncate">{conversation.title}</h3>
            </div>

            <div className="flex items-center justify-between">
              <div className="flex items-center gap-1 text-xs opacity-75">
                <Clock className="h-3 w-3" />
                <span>{new Date(conversation.updatedAt).toLocaleDateString("ko-KR")}</span>
              </div>
              <Badge
                variant={currentConversation?.id === conversation.id ? "secondary" : "outline"}
                className="text-xs"
              >
                {conversation.messages.length}
              </Badge>
            </div>
          </div>
        ))}

        {conversations.length === 0 && (
          <div className="text-center py-8 text-gray-500 dark:text-gray-400">
            <MessageSquare className="h-8 w-8 mx-auto mb-2 opacity-50" />
            <p className="text-sm">아직 대화가 없습니다</p>
            <p className="text-xs">새 대화를 시작해보세요</p>
          </div>
        )}
      </CardContent>
    </Card>
  )
}
