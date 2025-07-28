"use client";

import React, { useState, useRef, useEffect } from "react";
import { Plus, MessageCircle, FolderOpen, Zap, Search, Settings, ArrowUp, Menu, ArrowLeft, X } from "lucide-react";
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
    deleteRoom,
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
  const [deletingRoomId, setDeletingRoomId] = useState<string | null>(null);

  // account_db_key를 localStorage에서 읽어옴
  // const [accountDbKey, setAccountDbKey] = useState<string | null>(null);
  // useEffect(() => {
  //   const key = localStorage.getItem("account_db_key");
  //   setAccountDbKey(key);
  // }, []);

  // 스크롤 이벤트 핸들러
  const handleScroll = () => {
    if (!chatContainerRef.current) return;
    const { scrollTop, scrollHeight, clientHeight } = chatContainerRef.current;
    // 맨 아래에서 20px 이내면 autoScroll 유지
    setAutoScroll(scrollHeight - scrollTop - clientHeight < 20);
  };

  useEffect(() => {
    if (autoScroll && messagesEndRef.current && chatContainerRef.current) {
      setTimeout(() => {
        chatContainerRef.current?.scrollTo({
          top: chatContainerRef.current.scrollHeight,
          behavior: "smooth"
        });
      }, 100);
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

  // createRoom, fetchChatRooms 등에서 account_db_key를 포함해서 요청
  const handleNewChat = async () => {
    setShowPersonaModal(true);
  };
  const handleCreateRoomWithPersona = async () => {
    await createRoom(selectedPersona, `새 채팅 ${rooms.length + 1}`);
    setShowPersonaModal(false);
  };

  const handleSelectChat = (roomId: string) => {
    setCurrentRoomId(roomId);
  };

  const handleDeleteRoom = async (roomId: string) => {
    setDeletingRoomId(roomId);
    try {
      await deleteRoom(roomId);
    } finally {
      setDeletingRoomId(null);
    }
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
    <div className="h-screen w-full bg-gradient-to-br from-[#0a0a23] via-[#18181c] to-[#23243a] text-white flex overflow-hidden">
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
            className={`flex items-center gap-2 font-semibold transition-colors ${
              isLoading 
                ? 'text-gray-500 cursor-not-allowed' 
                : 'text-blue-400 hover:text-blue-300'
            }`}
            onClick={handleNewChat}
            disabled={isLoading}
          >
            <Plus size={16} />
            <span>새 채팅</span>
          </button>
        </div>
        {/* Navigation */}
        <div className="p-4 space-y-2">
          <div className={`flex items-center gap-2 py-2 ${
            isLoading 
              ? 'text-gray-500 cursor-not-allowed' 
              : 'text-gray-300 hover:text-white cursor-pointer'
          }`}>
            <MessageCircle size={16} />
            <span>채팅</span>
          </div>
          <div className={`flex items-center gap-2 py-2 ${
            isLoading 
              ? 'text-gray-500 cursor-not-allowed' 
              : 'text-gray-300 hover:text-white cursor-pointer'
          }`}>
            <FolderOpen size={16} />
            <span>프로젝트</span>
          </div>
          <div className={`flex items-center gap-2 py-2 ${
            isLoading 
              ? 'text-gray-500 cursor-not-allowed' 
              : 'text-gray-300 hover:text-white cursor-pointer'
          }`}>
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
                  className={`flex items-center group px-3 py-2 text-sm rounded truncate transition-all font-medium ${
                    currentRoomId === item.room_id
                      ? 'bg-gradient-to-r from-blue-500 to-indigo-600 text-white shadow'
                      : isLoading 
                        ? 'text-gray-500 cursor-not-allowed' 
                        : 'text-gray-300 hover:bg-[#23243a] cursor-pointer'
                  }`}
                >
                  <div
                    className="flex-1 truncate"
                    onClick={() => !isLoading && handleSelectChat(item.room_id)}
                  >
                    {item.title || "채팅방"}
                  </div>
                  <button
                    className="ml-2 p-1 rounded hover:bg-red-600/80 transition text-gray-400 hover:text-white opacity-0 group-hover:opacity-100 disabled:opacity-50"
                    onClick={e => { e.stopPropagation(); handleDeleteRoom(item.room_id); }}
                    disabled={deletingRoomId === item.room_id || isLoading}
                    title="채팅방 삭제"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          </div>
        </div>
        {/* Bottom Section */}
        <div className="p-4 border-t border-[#23243a]">
          <div className={`flex items-center gap-2 py-2 ${
            isLoading 
              ? 'text-gray-500 cursor-not-allowed' 
              : 'text-gray-300 hover:text-white cursor-pointer'
          }`}>
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
              onClick={() => !isLoading && setSidebarOpen(!sidebarOpen)}
              className={`p-2 rounded transition ${
                isLoading 
                  ? 'text-gray-500 cursor-not-allowed' 
                  : 'hover:bg-[#23243a]'
              }`}
              disabled={isLoading}
            >
              <Menu size={20} />
            </button>
            <span className="text-lg font-bold bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
              AI 트레이딩 챗
            </span>
          </div>
          <div className="flex items-center gap-2">
            <span className="text-xs text-gray-400">무료 요금제</span>
            <span className="text-xs bg-blue-600 px-2 py-1 rounded">업그레이드</span>
          </div>
        </div>
        {/* Chat Content - ChatGPT Style */}
        <div className="flex-1 flex flex-col w-full">
          {!currentRoomId ? (
            // 채팅방이 선택되지 않았을 때
            <div className="flex-1 flex flex-col items-center justify-center p-8">
              <div className="w-full max-w-2xl text-center">
                <h1 className="text-4xl font-light mb-2 bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">
                  {rooms.length === 0 ? "새 채팅방을 만들어보세요" : "채팅을 선택하세요"}
                </h1>
                {rooms.length === 0 && (
                  <p className="text-gray-400 text-lg mt-2">
                    왼쪽의 "새 채팅" 버튼을 클릭하여 AI와 대화를 시작하세요
                  </p>
                )}
              </div>
            </div>
          ) : (
            // 채팅방이 선택되었을 때 - ChatGPT 스타일
            <div className="flex-1 flex flex-col">
              {/* 메시지 영역 - 고정 높이 + 스크롤 */}
              <div
                ref={chatContainerRef}
                onScroll={handleScroll}
                className="overflow-y-auto scrollbar-hide"
                style={{ height: 'calc(100vh - 180px)' }}
              >
                {messages.length === 0 ? (
                  // 첫 메시지 안내
                  <div className="flex items-center justify-center h-full">
                    <div className="text-center text-gray-400">
                      <h2 className="text-xl font-medium mb-2">AI 트레이딩 어시스턴트</h2>
                      <p className="text-sm">아래에서 메시지를 입력하여 대화를 시작하세요</p>
                    </div>
                  </div>
                ) : (
                  // 메시지 목록
                  <div className="max-w-4xl mx-auto">
                    {messages.map((msg) => (
                      <ChatMessage
                        key={msg.id}
                        message={{
                          ...msg,
                          role: msg.role === "user" ? "user" : "assistant"
                        }}
                      />
                    ))}
                    {/* 로딩 인디케이터 - AI 답변 스타일 */}
                    {isLoading && (
                      <div className="w-full py-8 border-b border-gray-800">
                        <div className="max-w-4xl mx-auto px-4">
                          <div className="text-gray-400 text-base flex items-center gap-3 opacity-70">
                            <div className="w-5 h-5 border-2 border-gray-400 border-t-transparent rounded-full animate-spin"></div>
                            <span>AI가 응답을 생성하고 있습니다...</span>
                          </div>
                        </div>
                      </div>
                    )}
                    <div ref={messagesEndRef} />
                  </div>
                )}
              </div>
              {error && <div className="text-red-400 text-sm text-center p-4">{error}</div>}
            </div>
          )}
        </div>
        {/* Input Area - ChatGPT Style */}
        <div className="border-t border-gray-800 bg-black/60 backdrop-blur-xl">
          <div className="max-w-4xl mx-auto p-4">
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
                placeholder={currentRoomId ? "메시지를 입력하세요..." : "채팅방을 선택하거나 새로 만들어주세요"}
                className="w-full bg-gray-800 border border-gray-700 rounded-2xl px-4 py-3 pr-12 text-white placeholder-gray-400 focus:outline-none focus:border-blue-500 focus:ring-1 focus:ring-blue-500 transition-all"
                disabled={isLoading || !currentRoomId}
              />
              <button
                onClick={handleSubmit}
                disabled={isLoading || !message.trim() || !currentRoomId}
                className="absolute right-2 top-1/2 transform -translate-y-1/2 p-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed rounded-xl transition-all"
              >
                <ArrowUp size={16} />
              </button>
            </div>
            {/* 간단한 안내 */}
            <div className="text-center mt-2 text-xs text-gray-500">
              AI 트레이딩 어시스턴트와 자유롭게 대화하세요
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
