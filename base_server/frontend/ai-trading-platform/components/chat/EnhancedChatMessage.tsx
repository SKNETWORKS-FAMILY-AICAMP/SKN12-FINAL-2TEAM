"use client";

import React, { useState } from "react";
import TVMiniWidget from "./TVMiniWidget";
import TVAdvancedChart from "./TVAdvancedChart";

interface ChatMessage {
  id: string;
  role: "user" | "assistant";
  content: string;
  timestamp: Date;
  chart?: {
    symbols: string[];
    type: "mini" | "advanced";
    reason?: string;
  };
}

interface EnhancedChatMessageProps {
  message: ChatMessage;
  theme?: "light" | "dark";
}

export function EnhancedChatMessage({ message, theme = "dark" }: EnhancedChatMessageProps) {
  const [showChart, setShowChart] = useState(false);
  
  // AI 메시지에서 차트 정보 확인
  const isAI = message.role === "assistant";
  const hasChart = isAI && message.chart && message.chart.symbols && message.chart.symbols.length > 0;

  return (
    <div className={`flex ${message.role === "user" ? "justify-end" : "justify-start"} mb-4`}>
      <div className={`max-w-3xl ${message.role === "user" ? "order-2" : "order-1"}`}>
        {/* 메시지 버블 */}
        <div
          className={`rounded-2xl px-4 py-3 shadow-lg ${
            message.role === "user"
              ? "bg-blue-600 text-white"
              : "bg-gray-800 text-white border border-gray-700"
          }`}
        >
          <div className="whitespace-pre-wrap">{message.content}</div>
          
          {/* 차트 토글 버튼 (AI 메시지에 차트 정보가 있는 경우) */}
          {hasChart && (
            <div className="mt-3 pt-2 border-t border-gray-600">
              <button
                onClick={() => setShowChart(!showChart)}
                className="text-xs text-blue-400 hover:text-blue-300 transition-colors flex items-center gap-1"
              >
                {showChart ? "📊 차트 숨기기" : "📊 차트 보기"}
                <span className="text-gray-500">
                  ({message.chart!.symbols.length}개 종목: {message.chart!.symbols.map(s => s.split(':')[1] || s).join(", ")})
                </span>
              </button>
            </div>
          )}
        </div>
        
        {/* 차트 영역 */}
        {hasChart && showChart && (
          <div className="mt-3 rounded-xl overflow-hidden border border-gray-700 bg-gray-900" style={{ aspectRatio: "10/4", minHeight: "200px" }}>
            {message.chart!.type === "mini" && message.chart!.symbols.length > 0 && (
              <div className="p-2 h-full">
                <div className="text-xs text-gray-400 mb-2 px-2">
                  📈 {message.chart!.reason || `${message.chart!.symbols[0].split(':')[1] || message.chart!.symbols[0]} 차트`} (6개월)
                </div>
                <div className="h-full">
                  <TVMiniWidget 
                    symbol={message.chart!.symbols[0]} 
                    theme={theme}
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
                    theme={theme}
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
                        theme={theme}
                        dateRange="1M"
                      />
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}
        
        {/* 타임스탬프 */}
        <div className={`text-xs text-gray-500 mt-1 ${message.role === "user" ? "text-right" : "text-left"}`}>
          {message.timestamp.toLocaleTimeString('ko-KR', { 
            hour: '2-digit', 
            minute: '2-digit' 
          })}
        </div>
      </div>
    </div>
  );
}

// 사용 예시 컴포넌트 (서버 응답 시뮬레이션)
export function ChatExample() {
  const sampleMessages: ChatMessage[] = [
    {
      id: "1",
      role: "user",
      content: "애플 주식 어때?",
      timestamp: new Date()
    },
    {
      id: "2",
      role: "assistant",
      content: "애플(AAPL) 주식은 현재 기술적 분석상 상승 추세에 있습니다. RSI 지표를 보면 과매수 구간에 있지만, 이동평균선을 상향 돌파하며 강한 모멘텀을 보이고 있습니다. 단기적으로는 180달러 지지선을 확인해야 할 것 같습니다.",
      timestamp: new Date(),
      chart: {
        symbols: ["NASDAQ:AAPL"],
        type: "advanced",
        reason: "애플 주식 기술적 분석"
      }
    },
    {
      id: "3",
      role: "user",
      content: "테슬라와 엔비디아도 분석해줘",
      timestamp: new Date()
    },
    {
      id: "4",
      role: "assistant",
      content: "테슬라(TSLA)와 엔비디아(NVDA) 모두 AI 관련 수요 증가로 인한 긍정적인 전망입니다. 테슬라는 전기차 시장에서의 경쟁력이 강화되고 있고, 엔비디아는 AI 칩 수요 급증으로 실적이 크게 개선되고 있습니다. 두 종목 모두 기술적 분석상 상승 추세를 유지하고 있어 관심을 가져볼 만합니다.",
      timestamp: new Date(),
      chart: {
        symbols: ["NASDAQ:TSLA", "NASDAQ:NVDA"],
        type: "mini",
        reason: "테슬라와 엔비디아 주식 분석"
      }
    }
  ];

  return (
    <div className="max-w-4xl mx-auto p-4 bg-gray-950 min-h-screen">
      <h1 className="text-2xl font-bold text-white mb-6">AI 챗팅 + 서버 기반 TradingView 차트 예시</h1>
      
      <div className="space-y-4">
        {sampleMessages.map((message) => (
          <EnhancedChatMessage 
            key={message.id} 
            message={message} 
            theme="dark"
          />
        ))}
      </div>
    </div>
  );
}
