"use client";

import React, { useState, useRef, useEffect } from "react";
import { Plus, MessageCircle, FolderOpen, Zap, Search, Settings, ArrowUp, Menu, ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";

const MAX_CHATS = 10;

export default function ChatPage() {
  const [message, setMessage] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [chatHistoryItems, setChatHistoryItems] = useState<string[]>(["Old conversation"]);
  const [activeChat, setActiveChat] = useState<number>(0); // index of selected chat
  const [chatMessages, setChatMessages] = useState<Array<Array<{ from: "user" | "bot"; text: string }>>>([
    [
      { from: "bot", text: "안녕하세요! 무엇을 도와드릴까요?" }
    ]
  ]);
  const router = useRouter();
  const messagesEndRef = useRef<HTMLDivElement | null>(null);

  // Scroll to bottom when messages change or chat changes
  useEffect(() => {
    if (messagesEndRef.current) {
      messagesEndRef.current.scrollIntoView({ behavior: "smooth" });
    }
  }, [chatMessages, activeChat]);

  const handleSubmit = (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault();
    if (message.trim()) {
      // Add user message
      setChatMessages((prev) => {
        const updated = [...prev];
        updated[activeChat] = [...updated[activeChat], { from: "user", text: message }];
        return updated;
      });
      setMessage("");
      // Add bot reply after short delay
      setTimeout(() => {
        setChatMessages((prev) => {
          const updated = [...prev];
          const botReplies = [
            "좋은 질문입니다! 더 도와드릴까요?",
            "AI 챗봇이 답변 중입니다.",
            "자세한 정보를 원하시면 말씀해 주세요.",
            "트레이딩 관련 추가 질문이 있으신가요?"
          ];
          const reply = botReplies[Math.floor(Math.random() * botReplies.length)];
          updated[activeChat] = [...updated[activeChat], { from: "bot", text: reply }];
          return updated;
        });
      }, 700);
    }
  };

  const handleNewChat = () => {
    if (chatHistoryItems.length >= MAX_CHATS) return;
    const newTitle = `새 채팅 ${chatHistoryItems.filter(t => t.startsWith('새 채팅')).length + 1}`;
    setChatHistoryItems([newTitle, ...chatHistoryItems]);
    setChatMessages([[{ from: "bot", text: "안녕하세요! 무엇을 도와드릴까요?" }], ...chatMessages]);
    setActiveChat(0);
  };

  const handleSelectChat = (index: number) => {
    setActiveChat(index);
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#0a0a23] via-[#18181c] to-[#23243a] text-white flex">
      {/* Sidebar */}
      <div className={`${sidebarOpen ? 'w-80' : 'w-0'} transition-all duration-300 bg-black/40 border-r border-[#23243a] backdrop-blur-xl overflow-hidden flex flex-col`}>
        {/* Back Button */}
        <div className="p-4 border-b border-[#23243a] flex flex-col gap-2">
          <button
            className="flex items-center gap-2 text-gray-300 hover:text-white transition-colors font-semibold mb-2"
            onClick={() => router.push('/dashboard')}
          >
            <ArrowLeft size={18} />
            <span>뒤로가기</span>
          </button>
          <button
            className={`flex items-center gap-2 font-semibold transition-colors ${chatHistoryItems.length >= MAX_CHATS ? 'opacity-50 cursor-not-allowed' : 'text-blue-400 hover:text-blue-300'}`}
            onClick={handleNewChat}
            disabled={chatHistoryItems.length >= MAX_CHATS}
          >
            <Plus size={16} />
            <span>새 채팅</span>
          </button>
        </div>
        {/* Navigation */}
        <div className="p-4 space-y-2">
          <div className="flex items-center gap-2 text-gray-300 hover:text-white cursor-pointer py-2">
            <MessageCircle size={16} />
            <span>채팅</span>
          </div>
          <div className="flex items-center gap-2 text-gray-300 hover:text-white cursor-pointer py-2">
            <FolderOpen size={16} />
            <span>프로젝트</span>
          </div>
          <div className="flex items-center gap-2 text-gray-300 hover:text-white cursor-pointer py-2">
            <Zap size={16} />
            <span>아티팩트</span>
          </div>
        </div>
        {/* Recent History */}
        <div className="flex-1 overflow-y-auto">
          <div className="p-4">
            <h3 className="text-xs text-gray-400 mb-3 font-semibold tracking-wider">최근 항목</h3>
            <div className="space-y-1">
              {chatHistoryItems.map((item, index) => (
                <div
                  key={index}
                  className={`px-3 py-2 text-sm rounded cursor-pointer truncate transition-all font-medium ${
                    activeChat === index
                      ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow'
                      : 'text-gray-300 hover:bg-[#23243a]'
                  }`}
                  onClick={() => handleSelectChat(index)}
                >
                  {item}
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* Bottom Section */}
        <div className="p-4 border-t border-[#23243a]">
          <div className="flex items-center gap-2 text-gray-300 hover:text-white cursor-pointer py-2">
            <Settings size={16} />
            <span>설정</span>
          </div>
        </div>
      </div>
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between p-4 border-b border-[#23243a] bg-black/60 backdrop-blur-xl">
          <div className="flex items-center gap-4">
            <button 
              onClick={() => setSidebarOpen(!sidebarOpen)}
              className="p-2 hover:bg-[#23243a] rounded transition"
            >
              <Menu size={20} />
            </button>
            <span className="text-lg font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">AI 트레이딩 챗</span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">무료 요금제</span>
            <span className="text-xs bg-blue-600 px-2 py-1 rounded">업그레이드</span>
          </div>
        </div>
        {/* Chat Content */}
        <div className="flex-1 flex flex-col items-center justify-center p-8 w-full">
          <div className="w-full max-w-2xl">
            <div className="mb-8 text-center">
              <h1 className="text-4xl font-light mb-2 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                {chatHistoryItems[activeChat]}
              </h1>
            </div>
            <div className="flex flex-col gap-3 mb-8 max-h-[400px] min-h-[200px] overflow-y-auto bg-transparent p-2 rounded-lg scrollbar-hide">
              {chatMessages[activeChat]?.map((msg, idx) => (
                <div key={idx} className={`flex ${msg.from === "user" ? "justify-end" : "justify-start"}`}>
                  <div className={`px-4 py-2 rounded-xl max-w-xs break-words text-sm shadow ${msg.from === "user" ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100"}`}>
                    {msg.text}
                  </div>
                </div>
              ))}
              <div ref={messagesEndRef} />
            </div>
          </div>
        </div>
        {/* Input Area */}
        <div className="p-6 border-t border-[#23243a] bg-black/60 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto">
            <div className="relative">
              <input
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                placeholder="오늘 어떤 도움을 드릴까요?"
                className="w-full bg-[#18181c] border border-[#23243a] rounded-lg px-4 py-3 pr-12 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 shadow"
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    handleSubmit(e);
                  }
                }}
              />
              <button
                onClick={handleSubmit}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:opacity-90 rounded-lg transition-colors"
              >
                <ArrowUp size={16} />
              </button>
            </div>
          </div>
          {/* Footer */}
          <div className="flex items-center justify-between mt-4 text-xs text-gray-400">
            <div className="flex items-center gap-2">
              <span>업그레이드하여 도구 연결하기</span>
            </div>
            <div className="flex items-center gap-2">
              <span>Claude Sonnet 4</span>
              <button className="p-1 hover:bg-[#23243a] rounded">
                <ArrowUp size={12} />
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
