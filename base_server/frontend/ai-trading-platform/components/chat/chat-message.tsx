"use client";

import React from "react";
import DOMPurify from "dompurify";

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
}

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const content = message.content ?? "";
  const safeHtml = DOMPurify.sanitize(content);

  // 디버깅용 로그
  console.log("[ChatMessage] message:", message);
  console.log("[ChatMessage] role:", message.role, "isUser:", isUser);
  console.log("[ChatMessage] content (sanitized):", safeHtml);

  // 사용자 메시지만 풍선으로 표시
  if (isUser) {
    return (
      <div className="flex justify-end py-4">
        <div className="max-w-2xl">
          <div className="bg-blue-600 text-white rounded-2xl rounded-br-md px-4 py-2 text-sm break-words">
            {safeHtml}
          </div>
        </div>
      </div>
    );
  }

  // AI 답변은 전체 화면에 텍스트로 표시
  return (
    <div className="w-full py-8 border-b border-gray-800">
      <div className="max-w-4xl mx-auto px-4">
        <div 
          className="text-gray-100 text-base leading-relaxed prose prose-invert max-w-none"
          dangerouslySetInnerHTML={{ __html: safeHtml }}
        />
      </div>
    </div>
  );
}