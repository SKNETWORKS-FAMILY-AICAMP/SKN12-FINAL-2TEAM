"use client";

import React from "react";
import DOMPurify from "dompurify";
import TypingEffect from "./typing-effect";

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  isTyping?: boolean;
  onTypingUpdate?: () => void;
}

export default function ChatMessage({ message }: { message: Message }) {
  const isUser = message.role === "user";
  const content = message.content ?? "";
  const safeHtml = DOMPurify.sanitize(content);

  // 디버깅용 로그
  console.log("[ChatMessage] message:", message);
  console.log("[ChatMessage] role:", message.role, "isUser:", isUser);
  console.log("[ChatMessage] content (sanitized):", safeHtml);
  console.log("[ChatMessage] HTML 구조 분석:", safeHtml.includes('<li>'), safeHtml.includes('<strong>'));

  // 사용자 메시지만 풍선으로 표시
  if (isUser) {
    return (
      <div className="flex justify-end py-4">
        <div className="max-w-2xl">
        <div className="bg-gray-600/30 text-gray-100 rounded-2xl rounded-br-md px-4 py-2 text-sm break-words border border-gray-700/50">
            {safeHtml}
          </div>
        </div>
      </div>
    );
  }

  // AI 답변은 타이핑 효과와 함께 전체 화면에 텍스트로 표시
  if (message.isTyping) {
    return <TypingEffect 
      text={content} 
      onUpdate={message.onTypingUpdate}
    />;
  }
  
  return (
    <div className="w-full py-4 border-b border-gray-700/50">
      <div className="w-full px-4">
        <div 
          className="text-gray-100 text-base leading-6 max-w-none
                     [&>h1]:text-2xl [&>h1]:font-bold [&>h1]:mb-4 [&>h1]:text-blue-100 [&>h1]:tracking-tight
                     [&>h2]:text-xl [&>h2]:font-bold [&>h2]:mb-3 [&>h2]:text-green-100 [&>h2]:tracking-tight
                     [&>h3]:text-lg [&>h3]:font-semibold [&>h3]:mb-2 [&>h3]:text-yellow-100 [&>h3]:tracking-tight
                     [&>h4]:text-base [&>h4]:font-medium [&>h4]:mb-2 [&>h4]:text-purple-100 [&>h4]:tracking-tight
                     [&>p]:text-gray-200 [&>p]:mb-3 [&>p]:text-sm [&>p]:leading-6
                     [&>ul]:my-4 [&>ul]:space-y-1 [&>ul]:list-disc [&>ul]:list-inside [&>ul]:pl-3
                     [&>li]:text-green-300 [&>li]:mb-0.5 [&>li]:text-xs [&>li]:leading-4 [&>li]:font-mono [&>li]:tracking-wide
                     [&>strong]:text-blue-300 [&>strong]:font-bold [&>strong]:text-xs [&>strong]:font-mono
                     [&>em]:text-gray-300 [&>em]:italic"
          style={{
            '--tw-prose-li-font-size': '12px',
            '--tw-prose-li-line-height': '1rem',
            '--tw-prose-li-color': '#86efac',
            '--tw-prose-strong-color': '#93c5fd',
          } as React.CSSProperties}
          dangerouslySetInnerHTML={{ __html: safeHtml }}
        />
      </div>
    </div>
  );
}