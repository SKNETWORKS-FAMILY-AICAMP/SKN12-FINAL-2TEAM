"use client";

import React, { useState, useEffect, useRef } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { 
  TrendingUp, 
  TrendingDown, 
  Minus, 
  Play, 
  Pause, 
  RefreshCw,
  Globe,
  Building2,
  Activity
} from 'lucide-react';

interface StockData {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume?: number;
  market_cap?: number;
  high?: number;
  low?: number;
  open?: number;
  prev_close?: number;
  timestamp: string;
}

interface IndexData {
  name: string;
  code: string;
  value: number;
  change: number;
  change_pct: number;
  volume?: number;
  timestamp: string;
}

interface MarketStatus {
  korea_open: boolean;
  us_open: boolean;
}

interface PopularStock {
  symbol: string;
  name: string;
  market?: string;
}

export default function RealtimeStockTicker() {
  const [isStreaming, setIsStreaming] = useState(false);
  const [stockData, setStockData] = useState<StockData[]>([]);
  const [indexData, setIndexData] = useState<IndexData[]>([]);
  const [marketStatus, setMarketStatus] = useState<MarketStatus>({ korea_open: false, us_open: false });
  const [popularStocks, setPopularStocks] = useState<{ korean: PopularStock[], overseas: PopularStock[], indices: string[] }>({ 
    korean: [], 
    overseas: [], 
    indices: [] 
  });
  const [selectedStocks, setSelectedStocks] = useState<string[]>(['005930', '000660']);
  const [selectedIndices, setSelectedIndices] = useState<string[]>(['KOSPI', 'KOSDAQ']);
  const [customSymbol, setCustomSymbol] = useState('');
  const [error, setError] = useState<string | null>(null);
  const eventSourceRef = useRef<EventSource | null>(null);

  // 인기 종목 목록 가져오기
  useEffect(() => {
    fetchPopularStocks();
  }, []);

  const fetchPopularStocks = async () => {
    try {
      const response = await fetch('/api/realtime/popular-stocks');
      if (response.ok) {
        const data = await response.json();
        setPopularStocks(data);
      }
    } catch (error) {
      console.error('인기 종목 목록 조회 실패:', error);
    }
  };

  // 실시간 스트리밍 시작
  const startStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
    }

    const symbols = selectedStocks.join(',');
    const indices = selectedIndices.join(',');
    const url = `/api/realtime/stream?symbols=${symbols}&indices=${indices}`;

    eventSourceRef.current = new EventSource(url);
    setIsStreaming(true);
    setError(null);

    eventSourceRef.current.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        
        if (data.error) {
          setError(data.error);
          return;
        }

        if (data.stocks) {
          setStockData(data.stocks);
        }
        if (data.indices) {
          setIndexData(data.indices);
        }
        if (data.market_status) {
          setMarketStatus(data.market_status);
        }
      } catch (error) {
        console.error('스트림 데이터 파싱 오류:', error);
      }
    };

    eventSourceRef.current.onerror = (error) => {
      console.error('EventSource 오류:', error);
      setError('실시간 데이터 연결에 실패했습니다.');
      setIsStreaming(false);
    };
  };

  // 실시간 스트리밍 중지
  const stopStreaming = () => {
    if (eventSourceRef.current) {
      eventSourceRef.current.close();
      eventSourceRef.current = null;
    }
    setIsStreaming(false);
  };

  // 컴포넌트 언마운트 시 정리
  useEffect(() => {
    return () => {
      if (eventSourceRef.current) {
        eventSourceRef.current.close();
      }
    };
  }, []);

  // 종목 추가
  const addStock = () => {
    if (customSymbol && !selectedStocks.includes(customSymbol)) {
      setSelectedStocks([...selectedStocks, customSymbol]);
      setCustomSymbol('');
    }
  };

  // 종목 제거
  const removeStock = (symbol: string) => {
    setSelectedStocks(selectedStocks.filter(s => s !== symbol));
  };

  // 지수 추가/제거
  const toggleIndex = (index: string) => {
    if (selectedIndices.includes(index)) {
      setSelectedIndices(selectedIndices.filter(i => i !== index));
    } else {
      setSelectedIndices([...selectedIndices, index]);
    }
  };

  // 가격 변화에 따른 색상 결정 (한국 주식 시장 기준: 상승=빨강, 하락=파랑)
  const getPriceColor = (change: number, changePct: number) => {
    if (changePct > 0) return 'text-red-600';
    if (changePct < 0) return 'text-blue-600';
    return 'text-gray-600';
  };

  // 가격 변화에 따른 아이콘
  const getPriceIcon = (change: number, changePct: number) => {
    if (changePct > 0) return <TrendingUp className="w-4 h-4 text-red-600" />;
    if (changePct < 0) return <TrendingDown className="w-4 h-4 text-blue-600" />;
    return <Minus className="w-4 h-4 text-gray-600" />;
  };

  // 변동치 포맷팅 (부호 포함)
  const formatChange = (change: number) => {
    const sign = change > 0 ? '+' : change < 0 ? '' : '';
    return `${sign}${formatPrice(change)}`;
  };

  // 시장 상태 표시
  const getMarketStatusBadge = (isOpen: boolean) => {
    return (
      <Badge variant={isOpen ? "default" : "secondary"}>
        {isOpen ? "개장" : "폐장"}
      </Badge>
    );
  };

  // 숫자 포맷팅
  const formatNumber = (num: number) => {
    return new Intl.NumberFormat('ko-KR').format(num);
  };

  const formatPrice = (price: number) => {
    return new Intl.NumberFormat('ko-KR', { 
      minimumFractionDigits: 0,
      maximumFractionDigits: 2 
    }).format(price);
  };

  return (
    <div className="space-y-6">
      {/* 제목 및 컨트롤 */}
      <div className="flex items-center justify-between">
        <div className="flex items-center space-x-2">
          <Activity className="w-6 h-6 text-blue-600" />
          <h2 className="text-2xl font-bold">실시간 주식 시세</h2>
        </div>
        <div className="flex items-center space-x-2">
          {error && (
            <Badge variant="destructive" className="text-xs">
              {error}
            </Badge>
          )}
          <Button
            onClick={isStreaming ? stopStreaming : startStreaming}
            variant={isStreaming ? "destructive" : "default"}
            size="sm"
          >
            {isStreaming ? (
              <>
                <Pause className="w-4 h-4 mr-2" />
                중지
              </>
            ) : (
              <>
                <Play className="w-4 h-4 mr-2" />
                시작
              </>
            )}
          </Button>
        </div>
      </div>

      {/* 시장 상태 */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center space-x-2">
            <Globe className="w-5 h-5" />
            <span>시장 상태</span>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex space-x-4">
            <div className="flex items-center space-x-2">
              <Building2 className="w-4 h-4" />
              <span>한국 시장:</span>
              {getMarketStatusBadge(marketStatus.korea_open)}
            </div>
            <div className="flex items-center space-x-2">
              <Globe className="w-4 h-4" />
              <span>미국 시장:</span>
              {getMarketStatusBadge(marketStatus.us_open)}
            </div>
          </div>
        </CardContent>
      </Card>

      <Tabs defaultValue="stocks" className="w-full">
        <TabsList className="grid w-full grid-cols-2">
          <TabsTrigger value="stocks">주식</TabsTrigger>
          <TabsTrigger value="indices">지수</TabsTrigger>
        </TabsList>

        <TabsContent value="stocks" className="space-y-4">
          {/* 종목 선택 */}
          <Card>
            <CardHeader>
              <CardTitle>종목 선택</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex space-x-2">
                <Input
                  placeholder="종목 코드 입력 (예: 005930)"
                  value={customSymbol}
                  onChange={(e) => setCustomSymbol(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && addStock()}
                />
                <Button onClick={addStock} size="sm">추가</Button>
              </div>
              
              <div className="space-y-2">
                <Label>선택된 종목:</Label>
                <div className="flex flex-wrap gap-2">
                  {selectedStocks.map((symbol) => (
                    <Badge key={symbol} variant="outline" className="cursor-pointer" onClick={() => removeStock(symbol)}>
                      {symbol} ×
                    </Badge>
                  ))}
                </div>
              </div>

              <Separator />

              <div className="space-y-2">
                <Label>인기 종목:</Label>
                <ScrollArea className="h-32">
                  <div className="grid grid-cols-2 gap-2">
                    {popularStocks.korean.map((stock) => (
                      <Button
                        key={stock.symbol}
                        variant="ghost"
                        size="sm"
                        className="justify-start"
                        onClick={() => {
                          if (!selectedStocks.includes(stock.symbol)) {
                            setSelectedStocks([...selectedStocks, stock.symbol]);
                          }
                        }}
                      >
                        {stock.symbol} - {stock.name}
                      </Button>
                    ))}
                  </div>
                </ScrollArea>
              </div>
            </CardContent>
          </Card>

          {/* 주식 데이터 표시 */}
          <Card>
            <CardHeader>
              <CardTitle>실시간 주식 가격</CardTitle>
            </CardHeader>
            <CardContent>
              {stockData.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  실시간 데이터를 시작해주세요
                </div>
              ) : (
                <div className="space-y-2">
                  {stockData.map((stock) => (
                    <div key={stock.symbol} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-semibold">{stock.symbol}</div>
                        <div className="text-sm text-gray-600">
                          거래량: {formatNumber(stock.volume || 0)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-lg font-bold ${getPriceColor(stock.change, stock.change_pct)}`}>
                          {formatPrice(stock.price)}원
                        </div>
                        <div className={`flex items-center space-x-1 ${getPriceColor(stock.change, stock.change_pct)}`}>
                          {getPriceIcon(stock.change, stock.change_pct)}
                          <span>{formatChange(stock.change)} ({stock.change_pct >= 0 ? '+' : ''}{stock.change_pct.toFixed(2)}%)</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="indices" className="space-y-4">
          {/* 지수 선택 */}
          <Card>
            <CardHeader>
              <CardTitle>지수 선택</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 gap-2">
                {popularStocks.indices.map((index) => (
                  <Button
                    key={index}
                    variant={selectedIndices.includes(index) ? "default" : "outline"}
                    onClick={() => toggleIndex(index)}
                  >
                    {index}
                  </Button>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* 지수 데이터 표시 */}
          <Card>
            <CardHeader>
              <CardTitle>실시간 지수</CardTitle>
            </CardHeader>
            <CardContent>
              {indexData.length === 0 ? (
                <div className="text-center text-gray-500 py-8">
                  실시간 데이터를 시작해주세요
                </div>
              ) : (
                <div className="space-y-2">
                  {indexData.map((index) => (
                    <div key={index.code} className="flex items-center justify-between p-3 border rounded-lg">
                      <div className="flex-1">
                        <div className="font-semibold">{index.name}</div>
                        <div className="text-sm text-gray-600">
                          거래량: {formatNumber(index.volume || 0)}
                        </div>
                      </div>
                      <div className="text-right">
                        <div className={`text-lg font-bold ${getPriceColor(index.change, index.change_pct)}`}>
                          {formatPrice(index.value)}
                        </div>
                        <div className={`flex items-center space-x-1 ${getPriceColor(index.change, index.change_pct)}`}>
                          {getPriceIcon(index.change, index.change_pct)}
                          <span>{formatChange(index.change)} ({index.change_pct >= 0 ? '+' : ''}{index.change_pct.toFixed(2)}%)</span>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
} 