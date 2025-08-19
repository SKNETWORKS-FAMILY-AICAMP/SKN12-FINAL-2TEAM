"use client";

import React, { useState, useEffect } from "react";
import { Calendar, Clock, TrendingUp, TrendingDown, AlertTriangle } from "lucide-react";

interface EconomicEvent {
  date: string;
  time: string;
  country: string;
  event: string;
  impact: "High" | "Medium" | "Low";
  previous: string;
  forecast: string;
  actual?: string;
  currency?: string;
  change?: string;
  changePercentage?: string;
}

export function EconomicCalendarCard() {
  const [events, setEvents] = useState<EconomicEvent[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<number>(0);
  const [retryCount, setRetryCount] = useState(0);

  useEffect(() => {
    fetchEconomicCalendar();
  }, []);

  const fetchEconomicCalendar = async (forceRefresh: boolean = false) => {
    try {
      // 캐싱: 10분 이내라면 API 호출하지 않음
      const now = Date.now();
      const cacheTime = 10 * 60 * 1000; // 10분
      
      if (!forceRefresh && (now - lastFetch) < cacheTime && events.length > 0) {
        console.log("💾 캐시된 경제 일정 데이터 사용");
        return;
      }

      setLoading(true);
      
      // 백엔드 API 호출
      const response = await fetch('/api/dashboard/economic-calendar', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          accessToken: localStorage.getItem('accessToken') || '',
          days: 7
        })
      });
      
      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('API 호출 한도에 도달했습니다. 잠시 후 다시 시도해주세요.');
        }
        throw new Error('경제 일정 데이터를 가져올 수 없습니다.');
      }
      
      const data = await response.json();
      console.log("경제 일정 응답 데이터:", data);
      console.log("데이터 타입:", typeof data);
      console.log("데이터 키들:", Object.keys(data));
      console.log("data.result:", data.result);
      console.log("data.events:", data.events);
      console.log("data.events 타입:", typeof data.events);
      console.log("data.events 길이:", Array.isArray(data.events) ? data.events.length : '배열 아님');
      console.log("data.events 첫 번째 항목:", data.events?.[0]);
      
      // 백엔드 응답 구조에 맞게 수정
      // result가 'success'이거나 events 배열이 있으면 데이터 설정
      if (data.result === 'success' || (Array.isArray(data.events) && data.events.length > 0)) {
        if (Array.isArray(data.events)) {
          console.log("✅ 이벤트 배열 설정:", data.events);
          setEvents(data.events);
          setLastFetch(now);
          setRetryCount(0); // 성공 시 재시도 카운트 리셋
        } else {
          console.error("❌ data.events가 배열이 아님:", data.events);
          throw new Error('이벤트 데이터 형식이 올바르지 않습니다.');
        }
      } else {
        console.error("❌ API 응답 실패:", data.message);
        throw new Error(data.message || '데이터 조회 실패');
      }
    } catch (err) {
      console.error('경제 일정 조회 실패:', err);
      const errorMessage = err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.';
      setError(errorMessage);
      
      // 429 에러인 경우 재시도 지연
      if (errorMessage.includes('API 호출 한도')) {
        setRetryCount(prev => prev + 1);
      }
    } finally {
      setLoading(false);
    }
  };

  const handleRetry = () => {
    setError(null);
    fetchEconomicCalendar(true); // 강제 새로고침
  };

  const handleRefresh = () => {
    fetchEconomicCalendar(true); // 강제 새로고침
  };

  const getImpactColor = (impact: string) => {
    switch (impact) {
      case 'High': return 'text-red-400 bg-red-900/20';
      case 'Medium': return 'text-yellow-400 bg-yellow-900/20';
      case 'Low': return 'text-green-400 bg-green-900/20';
      default: return 'text-gray-400 bg-gray-900/20';
    }
  };

  const getImpactIcon = (impact: string) => {
    switch (impact) {
      case 'High': return <AlertTriangle className="w-3 h-3" />;
      case 'Medium': return <TrendingUp className="w-3 h-3" />;
      case 'Low': return <TrendingDown className="w-3 h-3" />;
      default: return <Clock className="w-3 h-3" />;
    }
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
        <div className="text-base font-bold mb-2 text-white">Economic Calendar</div>
        <div className="flex items-center justify-center w-full h-32">
          <div className="text-gray-400">로딩 중...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
        <div className="text-base font-bold mb-2 text-white">Economic Calendar</div>
        <div className="flex items-center justify-center w-full h-32">
          <div className="text-red-400 text-sm text-center">
            <div>{error}</div>
            <button 
              onClick={handleRetry}
              className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
            >
              재시도
            </button>
            <button 
              onClick={handleRefresh}
              className="mt-2 ml-2 px-3 py-1 bg-green-600 text-white rounded text-xs hover:bg-green-700"
            >
              새로고침
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
      <div className="text-base font-bold mb-2 text-white flex items-center gap-2">
        <Calendar className="w-4 h-4" />
        Economic Calendar
      </div>
      
      <div className="flex flex-col gap-2 w-full max-h-44 overflow-y-auto">
        {events.map((event, index) => (
          <div key={`${event.date}-${event.time}-${index}`} className="flex flex-col gap-1 p-2 bg-gray-800/50 rounded-lg">
            {/* 날짜와 시간 */}
            <div className="flex items-center justify-between text-xs text-gray-400">
              <span className="flex items-center gap-1">
                <Calendar className="w-3 h-3" />
                {event.date}
              </span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {event.time}
              </span>
            </div>
            
            {/* 국가와 이벤트명 */}
            <div className="flex items-center justify-between">
              <div className="flex-1">
                <div className="text-xs text-blue-400 font-medium">{event.country}</div>
                <div className="text-sm text-white font-semibold truncate">{event.event}</div>
              </div>
              
              {/* 영향도 배지 */}
              <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${getImpactColor(event.impact)}`}>
                {getImpactIcon(event.impact)}
                {event.impact}
              </div>
            </div>
            
            {/* 이전값과 예측값 */}
            <div className="flex items-center justify-between text-xs">
              <div className="flex items-center gap-2">
                <span className="text-gray-500">이전:</span>
                <span className="text-gray-300">{event.previous}</span>
              </div>
              <div className="flex items-center gap-2">
                <span className="text-gray-500">예측:</span>
                <span className="text-blue-300">{event.forecast}</span>
              </div>
            </div>
            
            {/* 추가 정보 (통화, 변동, 변동률) */}
            {(event.currency || event.change || event.changePercentage) && (
              <div className="flex items-center justify-between text-xs">
                {event.currency && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">통화:</span>
                    <span className="text-purple-300">{event.currency}</span>
                  </div>
                )}
                {event.change && event.change !== "N/A" && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">변동:</span>
                    <span className="text-orange-300">{event.change}</span>
                  </div>
                )}
                {event.changePercentage && event.changePercentage !== "N/A" && (
                  <div className="flex items-center gap-2">
                    <span className="text-gray-500">변동률:</span>
                    <span className="text-cyan-300">{event.changePercentage}%</span>
                  </div>
                )}
              </div>
            )}
            
            {/* 실제값 (있는 경우) */}
            {event.actual && (
              <div className="flex items-center gap-2 text-xs">
                <span className="text-gray-500">실제:</span>
                <span className="text-green-300 font-medium">{event.actual}</span>
              </div>
            )}
          </div>
        ))}
      </div>
      
      {/* 새로고침 버튼 */}
      <div className="w-full mt-2 pt-2 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs">
          <button 
            onClick={handleRefresh}
            className="text-blue-400 hover:text-blue-300 transition-colors"
          >
            새로고침 →
          </button>
          {lastFetch > 0 && (
            <span className="text-gray-500">
              마지막 업데이트: {new Date(lastFetch).toLocaleTimeString('ko-KR')}
            </span>
          )}
        </div>
      </div>
    </div>
  );
}
