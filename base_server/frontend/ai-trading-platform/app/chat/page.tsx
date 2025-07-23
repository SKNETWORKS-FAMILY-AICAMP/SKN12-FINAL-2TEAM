"use client";

import React, { useState, useRef, useEffect } from "react";
import { Plus, MessageCircle, FolderOpen, Zap, Search, Settings, ArrowUp, Menu, ArrowLeft } from "lucide-react";
import { useRouter } from "next/navigation";
import { useChat } from "@/hooks/use-chat";
import ChatMessage from "@/components/chat/chat-message";

// 타이핑 애니메이션 컴포넌트
function TypingMessage({ text }: { text: string }) {
  const [displayed, setDisplayed] = useState("");
  const idx = useRef(0);
  useEffect(() => {
    setDisplayed("");
    idx.current = 0;
    if (!text) return;
    const interval = setInterval(() => {
      setDisplayed((prev) => prev + text[idx.current]);
      idx.current++;
      if (idx.current >= text.length) clearInterval(interval);
    }, 18);
    return () => clearInterval(interval);
  }, [text]);
  return <span>{displayed}</span>;
}

// 메시지 버블 컴포넌트
function ChatBubble({ msg, isUser, isTyping }: { msg: any, isUser: boolean, isTyping?: boolean }) {
  return (
    <div className={`flex ${isUser ? "justify-end" : "justify-start"} animate-fadein`}>
      <div className={`px-4 py-2 rounded-xl max-w-xs break-words text-sm shadow ${isUser ? "bg-blue-600 text-white" : "bg-gray-800 text-gray-100"}`}>
        {isTyping ? <TypingMessage text={msg.message} /> : msg.message}
      </div>
    </div>
  );
}

export default function ChatPage() {
  const {
    rooms,
    currentRoomId,
    setCurrentRoomId,
    messages,
    isLoading,
    error,
    createRoom,
    sendMessage,
    personas,
    selectedPersona,
    setSelectedPersona,
  } = useChat();
  const [message, setMessage] = useState("");
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const router = useRouter();
  const chatContainerRef = useRef<HTMLDivElement | null>(null);
  const messagesEndRef = useRef<HTMLDivElement | null>(null);
  const [autoScroll, setAutoScroll] = useState(true);
  const inputRef = useRef<HTMLInputElement | null>(null);

  // Persona selection modal state
  const [showPersonaModal, setShowPersonaModal] = useState(false);

  // 스크롤 이벤트 핸들러
  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    // 맨 아래에서 20px 이내면 autoScroll 유지
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 20);
  };

  useEffect(() => {
    if (autoScroll && messagesEndRef.current) {
      setTimeout(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: "auto" });
      }, 0);
    }
  }, [messages, currentRoomId, autoScroll]);

  const handleSubmit = async (e: React.FormEvent | React.KeyboardEvent) => {
    e.preventDefault();
    if (message.trim() && !isLoading) {
      await sendMessage(message);
      setMessage("");
      if (inputRef.current) {
        inputRef.current.focus();
      }
    }
  };

  const handleNewChat = async () => {
    if (personas.length > 0) {
      setShowPersonaModal(true);
    } else {
      await createRoom(`새 채팅 ${rooms.length + 1}`);
    }
  };

  const handleCreateRoomWithPersona = async () => {
    await createRoom(`새 채팅 ${rooms.length + 1}`, selectedPersona || undefined);
    setShowPersonaModal(false);
  };

  const handleSelectChat = (roomId: string) => {
    setCurrentRoomId(roomId);
  };

  // 입력창 엔터/쉬프트+엔터 처리
  const handleInputKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  // 메시지 렌더링
  // 마지막 메시지가 AI이고 isLoading이면 타이핑 애니메이션 적용
  const lastMsgIdx = messages.length - 1;

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-[#0a0a23] via-[#18181c] to-[#23243a] text-white flex">
      {/* Persona Modal */}
      {showPersonaModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/60">
          <div className="bg-[#18181c] rounded-xl p-8 w-full max-w-md shadow-2xl border border-[#23243a]">
            <h2 className="text-xl font-bold mb-4 text-center">AI 페르소나 선택</h2>
            <div className="flex flex-col gap-4 mb-6">
              {personas.map((persona) => (
                <label key={persona.persona_id} className={`flex items-center gap-4 p-3 rounded-lg cursor-pointer border transition-all ${selectedPersona === persona.persona_id ? 'border-blue-500 bg-blue-900/20' : 'border-[#23243a] bg-[#23243a]/40'}`}>
                  <img src={persona.avatar_url} alt={persona.name} className="w-12 h-12 rounded-full object-cover border border-gray-700" />
                  <div className="flex-1">
                    <div className="font-semibold text-base">{persona.name}</div>
                    <div className="text-xs text-gray-400">{persona.description}</div>
                  </div>
                  <input
                    type="radio"
                    checked={selectedPersona === persona.persona_id}
                    onChange={() => setSelectedPersona(persona.persona_id)}
                    className="accent-blue-500 w-5 h-5"
                  />
                </label>
              ))}
            </div>
            <div className="flex gap-2 justify-end">
              <button
                className="px-4 py-2 rounded bg-gray-700 text-white hover:bg-gray-600 transition"
                onClick={() => setShowPersonaModal(false)}
                disabled={isLoading}
              >취소</button>
              <button
                className="px-4 py-2 rounded bg-gradient-to-r from-blue-500 to-indigo-600 text-white font-semibold hover:opacity-90 transition"
                onClick={handleCreateRoomWithPersona}
                disabled={isLoading || !selectedPersona}
              >선택하고 시작</button>
            </div>
          </div>
        </div>
      )}
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
            className={`flex items-center gap-2 font-semibold transition-colors text-blue-400 hover:text-blue-300`}
            onClick={handleNewChat}
            disabled={isLoading}
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
              {rooms.map((item) => (
                <div
                  key={item.room_id}
                  className={`px-3 py-2 text-sm rounded cursor-pointer truncate transition-all font-medium ${
                    currentRoomId === item.room_id
                      ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow'
                      : 'text-gray-300 hover:bg-[#23243a]'
                  }`}
                  onClick={() => handleSelectChat(item.room_id)}
                >
                  {item.room_name}
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
          <div className="w-full max-w-2xl h-full flex flex-col">
            <div className="mb-8 text-center">
              <h1 className="text-4xl font-light mb-2 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                {rooms.find((r) => r.room_id === currentRoomId)?.room_name || "채팅을 선택하세요"}
              </h1>
            </div>
            {/* 채팅 메시지 영역: 항상 아래 정렬 */}
            <div
              ref={chatContainerRef}
              onScroll={handleScroll}
              className="flex-1 flex flex-col justify-end gap-3 p-6 max-h-[60vh] min-h-[200px] overflow-y-auto bg-transparent scrollbar-hide"
            >
              {messages.map((msg) => (
                <ChatMessage
                  key={msg.id}
                  message={{
                    ...msg,
                    role: msg.role === "user" ? "user" : "assistant"
                  }}
                />
              ))}
              {/* 로딩 인디케이터 */}
              {isLoading && (
                <div className="flex justify-start animate-fadein">
                  <div className="px-4 py-2 rounded-xl max-w-xs break-words text-sm shadow bg-gray-800 text-gray-100 flex items-center gap-1">
                    <span className="animate-bounce">.</span>
                    <span className="animate-bounce delay-150">.</span>
                    <span className="animate-bounce delay-300">.</span>
                  </div>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>
            {error && <div className="text-red-400 text-sm text-center mb-2">{error}</div>}
          </div>
        </div>
        {/* Input Area */}
        <div className="p-6 border-t border-[#23243a] bg-black/60 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto">
            <div className="relative">
              <input
                ref={inputRef}
                type="text"
                value={message}
                onChange={(e) => setMessage(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmit(e);
                  }
                }}
                placeholder="메시지를 입력하세요..."
                className="w-full bg-[#18181c] border border-[#23243a] rounded-lg px-4 py-3 pr-12 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 shadow"
                disabled={isLoading}
              />
              <button
                onClick={handleSubmit}
                disabled={isLoading || !message.trim()}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-gradient-to-r from-blue-500 to-indigo-600 hover:opacity-90 disabled:opacity-50 rounded-lg transition-all"
              >
                <ArrowUp size={16} />
              </button>
            </div>
          </div>
          {/* Footer */}
          <div className="flex items-center justify-between mt-4 text-xs text-gray-400">
            <div className="flex items-center gap-2">

            </div>
            <div className="flex items-center gap-2">
              <span>업그레이드하여 도구 연결하기</span>
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
