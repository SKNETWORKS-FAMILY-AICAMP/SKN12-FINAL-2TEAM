"use client";

import React, { useState } from "react";
import { sendChatMessage, parseServerResponse } from "@/utils/chatUtils";
import ChatMessage from "@/components/chat/chat-message";

export default function ChatDebugPage() {
  const [messages, setMessages] = useState<any[]>([]);
  const [inputMessage, setInputMessage] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [sessionId, setSessionId] = useState("debug_session");

  const handleSendMessage = async () => {
    if (!inputMessage.trim()) return;

    setIsLoading(true);
    
    // 사용자 메시지 추가
    const userMessage = {
      id: `user_${Date.now()}`,
      content: inputMessage,
      role: "user" as const,
      timestamp: Date.now()
    };
    
    setMessages(prev => [...prev, userMessage]);
    setInputMessage("");

    try {
      // 서버에 메시지 전송
      const response = await sendChatMessage(inputMessage, sessionId);
      console.log("서버 응답:", response);
      
      // 서버 응답을 메시지로 변환
      const aiMessage = parseServerResponse(
        response, 
        `ai_${Date.now()}`,
        new Date()
      );
      
      console.log("변환된 AI 메시지:", aiMessage);
      setMessages(prev => [...prev, aiMessage]);
      
    } catch (error) {
      console.error("메시지 전송 실패:", error);
      // 에러 메시지 추가
      const errorMessage = {
        id: `error_${Date.now()}`,
        content: "메시지 전송에 실패했습니다.",
        role: "assistant" as const,
        timestamp: Date.now()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4 bg-gray-950 min-h-screen">
      <h1 className="text-2xl font-bold text-white mb-6">채팅 차트 디버깅</h1>
      
      {/* 메시지 목록 */}
      <div className="space-y-4 mb-6 max-h-96 overflow-y-auto">
        {messages.map((message) => (
          <ChatMessage 
            key={message.id} 
            message={message}
          />
        ))}
        {isLoading && (
          <div className="text-gray-400 text-center py-4">
            AI가 응답을 생성하고 있습니다...
          </div>
        )}
      </div>
      
      {/* 입력 영역 */}
      <div className="flex gap-2">
        <input
          type="text"
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && handleSendMessage()}
          placeholder="메시지를 입력하세요 (예: 애플 주식 어때?)"
          className="flex-1 px-4 py-2 bg-gray-800 text-white rounded-lg border border-gray-700 focus:outline-none focus:border-blue-500"
          disabled={isLoading}
        />
        <button
          onClick={handleSendMessage}
          disabled={isLoading || !inputMessage.trim()}
          className="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed"
        >
          전송
        </button>
      </div>
      
      {/* 세션 ID */}
      <div className="mt-4">
        <label className="text-gray-400 text-sm">세션 ID:</label>
        <input
          type="text"
          value={sessionId}
          onChange={(e) => setSessionId(e.target.value)}
          className="ml-2 px-2 py-1 bg-gray-800 text-white rounded border border-gray-700 text-sm"
        />
      </div>
      
      {/* 디버깅 정보 */}
      <div className="mt-6 p-4 bg-gray-900 rounded-lg">
        <h3 className="text-white font-semibold mb-2">디버깅 정보</h3>
        <div className="text-gray-400 text-sm space-y-1">
          <div>총 메시지 수: {messages.length}</div>
          <div>AI 메시지 수: {messages.filter(m => m.role === 'assistant').length}</div>
          <div>차트 포함 메시지 수: {messages.filter(m => m.chart).length}</div>
        </div>
      </div>
    </div>
  );
}
