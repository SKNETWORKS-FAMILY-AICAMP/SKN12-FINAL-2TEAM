"use client";

import React, { useState } from "react";
import DOMPurify from "dompurify";
import TypingEffect from "./typing-effect";
import TVMiniWidget from "./TVMiniWidget";
import TVAdvancedChart from "./TVAdvancedChart";

interface Message {
  id: string;
  content: string;
  role: "user" | "assistant";
  isTyping?: boolean;
  onTypingUpdate?: () => void;
  chart?: {
    symbols: string[];
    type: "mini" | "advanced";
    reason?: string;
  };
}

export default function ChatMessage({ message }: { message: Message }) {
  const [showChart, setShowChart] = useState(false);
  const isUser = message.role === "user";
  const content = message.content ?? "";
  const safeHtml = DOMPurify.sanitize(content);

  // AI 메시지에서 차트 정보 확인
  const hasChart = !isUser && message.chart && message.chart.symbols && message.chart.symbols.length > 0;

  // 디버깅용 로그
  console.log("[ChatMessage] message:", message);
  console.log("[ChatMessage] role:", message.role, "isUser:", isUser);
  console.log("[ChatMessage] content (sanitized):", safeHtml);
  console.log("[ChatMessage] chart info:", message.chart);
  console.log("[ChatMessage] hasChart:", hasChart);

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
        
        {/* 차트 토글 버튼 (AI 메시지에 차트 정보가 있는 경우) */}
        {hasChart && (
          <div className="mt-4 pt-3 border-t border-gray-700">
            <button
              onClick={() => setShowChart(!showChart)}
              className="text-sm text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-2"
            >
              {showChart ? "📊 차트 숨기기" : "📊 차트 보기"}
              <span className="text-gray-500 text-xs">
                ({message.chart!.symbols.length}개 종목: {message.chart!.symbols.map(s => s.split(':')[1] || s).join(", ")})
              </span>
            </button>
          </div>
        )}
        
        {/* 차트 영역 */}
        {hasChart && showChart && (
          <div className="mt-4 rounded-xl overflow-hidden border border-gray-700 bg-gray-900" style={{ aspectRatio: "10/4", minHeight: "200px" }}>
            {message.chart!.type === "mini" && message.chart!.symbols.length > 0 && (
              <div className="p-2 h-full">
                <div className="text-xs text-gray-400 mb-2 px-2">
                  📈 {message.chart!.reason || `${message.chart!.symbols[0].split(':')[1] || message.chart!.symbols[0]} 차트`} (6개월)
                </div>
                <div className="h-full">
                  <TVMiniWidget 
                    symbol={message.chart!.symbols[0]} 
                    theme="dark"
                    dateRange="6M"
                  />
                </div>
              </div>
            )}
            
            {message.chart!.type === "advanced" && message.chart!.symbols.length > 0 && (
              <div className="p-2 h-full">
                <div className="text-xs text-gray-400 mb-2 px-2">
                  📊 {message.chart!.reason || `${message.chart!.symbols[0].split(':')[1] || message.chart!.symbols[0]} 고급 차트`}
                </div>
                <div className="h-full">
                  <TVAdvancedChart 
                    symbol={message.chart!.symbols[0]} 
                    theme="dark"
                    interval="D"
                  />
                </div>
              </div>
            )}
            
            {/* 여러 종목이 있는 경우 미니 차트로 표시 */}
            {message.chart!.symbols.length > 1 && (
              <div className="p-2 border-t border-gray-700">
                <div className="text-xs text-gray-400 mb-2 px-2">
                  📈 관련 종목들
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-2">
                  {message.chart!.symbols.slice(1, 3).map((symbol, index) => (
                    <div key={index} className="h-24" style={{ aspectRatio: "10/4" }}>
                      <TVMiniWidget 
                        symbol={symbol} 
                        theme="dark"
                        dateRange="1M"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
      </div>
    </div>
  );
}