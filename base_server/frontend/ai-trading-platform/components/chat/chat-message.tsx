"use client"

import type React from "react";

export function ChatMessage({ message }: { message: { id: string; content: string; role: string } }) {
  const isUser = message.role === "user";
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} animate-fadein my-2`}>
      <div
        className={`px-4 py-2 rounded-xl max-w-xs md:max-w-md break-words text-sm shadow transition-all
          ${isUser ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100"}`}
      >
        {message.content}
      </div>
    </div>
  );
}
