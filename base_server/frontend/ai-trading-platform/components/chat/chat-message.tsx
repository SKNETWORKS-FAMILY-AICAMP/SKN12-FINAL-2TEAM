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

  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} my-2`}>
      <div
        className={`px-4 py-2 rounded-xl max-w-xs md:max-w-md break-words text-sm shadow
        ${isUser ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100"} prose prose-sm prose-invert max-w-none`}
        dangerouslySetInnerHTML={{ __html: safeHtml }}
      />
    </div>
  );
}