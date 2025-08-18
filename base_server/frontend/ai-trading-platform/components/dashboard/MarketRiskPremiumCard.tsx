"use client";

import React, { useState, useEffect } from "react";
import { TrendingUp, TrendingDown, Globe, AlertTriangle } from "lucide-react";

interface MarketRiskPremium {
  country: string;
  countryCode: string;
  continent: string;
  countryRiskPremium: number;
  totalEquityRiskPremium: number;
}

export function MarketRiskPremiumCard() {
  const [premiums, setPremiums] = useState<MarketRiskPremium[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [lastFetch, setLastFetch] = useState<number>(0);

  useEffect(() => {
    fetchMarketRiskPremiums();
  }, []);

  const fetchMarketRiskPremiums = async () => {
    try {
      setLoading(true);
      
      const response = await fetch('/api/dashboard/market-risk-premium', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          accessToken: localStorage.getItem('accessToken') || '',
          countries: ["US", "KR", "JP", "CN", "EU"]
        })
      });
      
      if (!response.ok) {
        throw new Error('시장 위험 프리미엄 데이터를 가져올 수 없습니다.');
      }
      
      const data = await response.json();
      console.log("시장 위험 프리미엄 응답 데이터:", data);
      
      if (data.result === 'success') {
        setPremiums(data.premiums || []);
        setLastFetch(Date.now());
      } else {
        throw new Error(data.message || '데이터 조회 실패');
      }
    } catch (err) {
      console.error('시장 위험 프리미엄 조회 실패:', err);
      setError(err instanceof Error ? err.message : '알 수 없는 오류가 발생했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const getRiskLevel = (premium: number) => {
    if (premium <= 2.0) return { level: "Low", color: "text-green-400 bg-green-900/20" };
    if (premium <= 4.0) return { level: "Medium", color: "text-yellow-400 bg-yellow-900/20" };
    return { level: "High", color: "text-red-400 bg-red-900/20" };
  };

  const getRiskIcon = (premium: number) => {
    if (premium <= 2.0) return <TrendingDown className="w-3 h-3" />;
    if (premium <= 4.0) return <TrendingUp className="w-3 h-3" />;
    return <AlertTriangle className="w-3 h-3" />;
  };

  if (loading) {
    return (
      <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
        <div className="text-base font-bold mb-2 text-white">Market Risk Premium</div>
        <div className="flex items-center justify-center w-full h-32">
          <div className="text-gray-400">로딩 중...</div>
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
        <div className="text-base font-bold mb-2 text-white">Market Risk Premium</div>
        <div className="flex items-center justify-center w-full h-32">
          <div className="text-red-400 text-sm text-center">
            <div>{error}</div>
            <button 
              onClick={fetchMarketRiskPremiums}
              className="mt-2 px-3 py-1 bg-blue-600 text-white rounded text-xs hover:bg-blue-700"
            >
              재시도
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="bg-gradient-to-br from-gray-950 via-gray-900 to-gray-800 rounded-xl shadow-lg p-3 min-w-[400px] flex flex-col items-start w-full max-w-md border border-gray-800 h-53">
      <div className="text-base font-bold mb-2 text-white flex items-center gap-2">
        <Globe className="w-4 h-4" />
        Market Risk Premium
      </div>
      
      <div className="flex flex-col gap-2 w-full max-h-44 overflow-y-auto">
        {premiums.map((premium, index) => {
          const countryRisk = getRiskLevel(premium.countryRiskPremium);
          const equityRisk = getRiskLevel(premium.totalEquityRiskPremium);
          
          return (
            <div key={`${premium.countryCode}-${index}`} className="flex flex-col gap-1 p-2 bg-gray-800/50 rounded-lg">
              {/* 국가와 대륙 */}
              <div className="flex items-center justify-between">
                <div className="flex-1">
                  <div className="text-xs text-blue-400 font-medium">{premium.country}</div>
                  <div className="text-xs text-gray-400">{premium.continent}</div>
                </div>
              </div>
              
              {/* 국가 위험 프리미엄 */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">국가 위험:</span>
                <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${countryRisk.color}`}>
                  {getRiskIcon(premium.countryRiskPremium)}
                  {premium.countryRiskPremium}%
                </div>
              </div>
              
              {/* 총 주식 위험 프리미엄 */}
              <div className="flex items-center justify-between text-xs">
                <span className="text-gray-500">총 주식 위험:</span>
                <div className={`px-2 py-1 rounded-full text-xs font-medium flex items-center gap-1 ${equityRisk.color}`}>
                  {getRiskIcon(premium.totalEquityRiskPremium)}
                  {premium.totalEquityRiskPremium}%
                </div>
              </div>
            </div>
          );
        })}
      </div>
      
      {/* 새로고침 버튼 */}
      <div className="w-full mt-2 pt-2 border-t border-gray-700">
        <div className="flex items-center justify-between text-xs">
          <button 
            onClick={fetchMarketRiskPremiums}
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
