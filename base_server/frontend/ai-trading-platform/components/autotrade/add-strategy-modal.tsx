"use client"

import React, { useState, useEffect, useCallback } from "react";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { Search, X, Loader2 } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { searchStocks, getStockDetail } from "@/lib/api/stocks";

interface StockInfo {
  symbol: string;
  name: string;
  description: string;
  currentPrice: number;
  marketCap: string;
  sector: string;
  outlook: number; // 1-100
  confidence: number; // 1-100
}

interface AddStrategyModalProps {
  isOpen: boolean;
  onClose: () => void;
  onAddStrategy: (strategy: any) => void;
}

// 폴백용 샘플 주식 데이터 (API 실패 시 사용)
const fallbackStocksRaw = [
  {
    symbol: "005930",
    name: "삼성전자",
    description: "세계 최대 반도체 및 스마트폰 제조업체",
    currentPrice: 68500,
    marketCap: "4,200조원",
    sector: "반도체",
  },
  {
    symbol: "000660",
    name: "SK하이닉스",
    description: "메모리 반도체 전문 제조업체",
    currentPrice: 115000,
    marketCap: "850조원",
    sector: "반도체",
  },
  {
    symbol: "035420",
    name: "NAVER",
    description: "한국 최대 인터넷 포털 및 IT 기업",
    currentPrice: 185000,
    marketCap: "320조원",
    sector: "인터넷",
  },
  {
    symbol: "035720",
    name: "카카오",
    description: "모바일 플랫폼 및 디지털 콘텐츠 기업",
    currentPrice: 48500,
    marketCap: "220조원",
    sector: "인터넷",
  },
  {
    symbol: "051910",
    name: "LG화학",
    description: "배터리 및 화학 소재 전문 기업",
    currentPrice: 420000,
    marketCap: "380조원",
    sector: "화학",
  },
];
const fallbackStocks = fallbackStocksRaw.filter(
  stock => stock && stock.symbol && typeof stock.symbol === 'string' && stock.symbol.trim()
);

export function AddStrategyModal({ isOpen, onClose, onAddStrategy }: AddStrategyModalProps) {
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStock, setSelectedStock] = useState<StockInfo | null>(null);
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [searchError, setSearchError] = useState("");

  // 디바운스된 검색 함수
  const debouncedSearch = useCallback(
    debounce(async (query: string) => {
      if (!query.trim()) {
        setSearchResults([]);
        return;
      }

      setIsSearching(true);
      setSearchError("");

      try {
        // 실제 API 호출
        const response = await searchStocks(query) as any;
        
        const list = Array.isArray(response?.results) ? response.results : []
        if (response?.errorCode === 0 && list.length > 0) {
          // 백엔드 API 응답 구조에 맞춰 데이터 변환 (네이버 스타일, 달러 단위)
          const stocks = list
            .filter((security: any) => security && security.symbol && security.symbol.trim()) // null/undefined symbol 필터링
            .map((security: any) => ({
              symbol: security.symbol,
              name: security.name,
              description: security.industry || security.sector || "",
              currentPrice: security.current_price,
              marketCap: security.market_cap
                ? `$${Number(security.market_cap).toLocaleString()}`
                : "N/A",
              sector: security.sector || "N/A",
            }));
          setSearchResults(stocks);
        } else {
          // API 실패 시 폴백 데이터 사용
          const filteredFallback = fallbackStocks.filter(stock =>
            stock && stock.symbol && typeof stock.symbol === 'string' && stock.symbol.trim() &&
            (stock.name.toLowerCase().includes(query.toLowerCase()) ||
             stock.symbol.includes(query))
          );
          setSearchResults(filteredFallback);
        }
      } catch (error) {
        console.error("주식 검색 실패:", error);
        setSearchError("검색 중 오류가 발생했습니다. 다시 시도해주세요.");
        
        // 에러 시에도 폴백 데이터 사용
        const filteredFallback = fallbackStocks.filter(stock =>
          stock && stock.symbol && typeof stock.symbol === 'string' && stock.symbol.trim() &&
          (stock.name.toLowerCase().includes(query.toLowerCase()) ||
           stock.symbol.includes(query))
        );
        setSearchResults(filteredFallback);
      } finally {
        setIsSearching(false);
      }
    }, 300),
    []
  );

  // 검색어 변경 시 API 호출
  useEffect(() => {
    debouncedSearch(searchTerm);
  }, [searchTerm, debouncedSearch]);

  // 검색어가 비어지면 선택된 기업 자동 해제
  useEffect(() => {
    // 선택된 기업이 현재 검색 결과에 없으면 자동 해제
    if (selectedStock && searchResults.length > 0) {
      const isSelectedStockInResults = searchResults.some(
        (stock: any) => stock.symbol === selectedStock.symbol
      );
      
      if (!isSelectedStockInResults) {
        console.log("선택된 기업이 목록에 없어서 자동 해제:", selectedStock.symbol);
        setSelectedStock(null);
      }
    }
  }, [searchResults, selectedStock]);

  const handleStockSelect = async (stock: any) => {
    try {
      // stock과 symbol 유효성 검사
      if (!stock || !stock.symbol) {
        console.error("유효하지 않은 stock 정보:", stock);
        setSelectedStock({
          symbol: "UNKNOWN",
          name: "알 수 없는 기업",
          description: "",
          currentPrice: 0,
          marketCap: "N/A",
          sector: "N/A",
          outlook: 70,
          confidence: 80,
        });
        return;
      }
      
      // symbol이 string인지 확인하고 변환
      const symbol = typeof stock.symbol === 'string' ? stock.symbol : String(stock.symbol);
      
      // symbol이 비어있지 않은지 확인
      if (!symbol.trim()) {
        console.error("빈 symbol:", symbol);
        setSelectedStock({
          ...stock,
          outlook: 70,
          confidence: 80,
        });
        return;
      }
      
      // 선택된 주식의 상세 정보 가져오기
      const detailResponse = await getStockDetail(symbol) as any;
      
      let stockInfo: StockInfo;
      // 더 강력한 null 체크
      if (detailResponse && 
          detailResponse.errorCode === 0 && 
          detailResponse.price_data && 
          typeof detailResponse.price_data === 'object' ) {
        // API에서 받은 상세 정보 사용
        const priceData = detailResponse.price_data[symbol] || detailResponse.price_data.default || detailResponse.price_data
        stockInfo = {
          ...stock,
          currentPrice: (priceData && (priceData.close_price || priceData.current_price)) || stock.currentPrice,
          outlook: 70,
          confidence: 80,
        };
      } else {
        // 폴백 데이터 사용
        stockInfo = {
          ...stock,
          outlook: 70, // 기본값
          confidence: 80, // 기본값
        };
      }
      
      setSelectedStock(stockInfo);
    } catch (error) {
      console.error("주식 상세 정보 조회 실패:", error);
      // 에러 시에도 기본 정보로 설정
      setSelectedStock({
        ...stock,
        outlook: 70, // 기본값
        confidence: 80, // 기본값
      });
    }
  };

  const handleAddStrategy = () => {
    if (!selectedStock) return;

    const newStrategy = {
      id: Date.now(),
      name: `${selectedStock.name} 투자 전략`,
      subtitle: `${selectedStock.symbol} - ${selectedStock.sector} 섹터`,
      philosophy: `${selectedStock.name}의 ${selectedStock.description}을 바탕으로 한 중장기 투자 전략`,
      profit: "+0.0%",
      profitColor: "text-gray-400",
      winRate: "0%",
      trades: 0,
      recent: new Date().toLocaleString('ko-KR', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit',
        hour: '2-digit',
        minute: '2-digit'
      }),
      statusColor: "bg-blue-500",
      isActive: true,
      stockInfo: selectedStock,
    };

    onAddStrategy(newStrategy);
    onClose();
    resetForm();
  };

  const resetForm = () => {
    setSearchTerm("");
    setSelectedStock(null);
    setSearchResults([]);
    setSearchError("");
  };

  // 영어 알파벳만 허용하는 함수
  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    // 영어 알파벳, 공백, 점(.)만 허용
    const englishOnly = value.replace(/[^a-zA-Z\s.]/g, '');
    setSearchTerm(englishOnly);
  };

  return (
    <AnimatePresence>
      {isOpen && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="fixed inset-0 z-50 flex items-center justify-center bg-black/60 backdrop-blur-sm"
        >
          <motion.div
            initial={{ scale: 0.9, y: 20 }}
            animate={{ scale: 1, y: 0 }}
            exit={{ scale: 0.9, y: 20 }}
            className="bg-[#0f172a] rounded-2xl p-6 w-full max-w-4xl max-h-[95vh] overflow-y-auto border border-gray-800"
          >
            {/* Header */}
            <div className="flex items-center justify-between mb-6">
              <div>
                <h2 className="text-2xl font-bold text-white">새 기업 추가하기</h2>
                <p className="text-muted-foreground mt-1">투자할 기업을 선택하고 매매 시그널을 설정하세요</p>
              </div>
              <Button
                variant="ghost"
                size="icon"
                onClick={onClose}
                className="rounded-full hover:bg-white/10"
              >
                <X className="w-4 h-4" />
              </Button>
            </div>

            {/* Stock Search */}
            <div className="space-y-4 mb-6">
              <div>
                <Label className="text-white mb-2 block">기업 검색</Label>
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4" />
                  <Input
                    placeholder="기업명 또는 종목코드 입력 (영어만 가능)..."
                    value={searchTerm}
                    onChange={handleSearchInputChange}
                    className="pl-10 bg-[#1e293b] border-gray-700 text-white"
                  />
                  {isSearching && (
                    <Loader2 className="absolute right-3 top-1/2 transform -translate-y-1/2 text-muted-foreground w-4 h-4 animate-spin" />
                  )}
                </div>
                {searchError && (
                  <p className="text-red-400 text-sm mt-2">{searchError}</p>
                )}
              </div>

              {/* Search Results */}
              {searchTerm && (
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {searchResults.length > 0 ? (
                    searchResults.map((stock) => (
                      <Card
                        key={stock.symbol}
                        className={`cursor-pointer transition-all ${
                          selectedStock?.symbol === stock.symbol
                            ? "bg-blue-500/20 border-blue-500"
                            : "bg-[#1e293b] border-gray-700 hover:bg-[#334155]"
                        }`}
                        onClick={() => handleStockSelect(stock)}
                      >
                        <CardContent className="p-3">
                          <div className="flex items-center justify-between">
                            <div>
                              <div className="flex items-center gap-2">
                                <h3 className="font-semibold text-white">{stock.name}</h3>
                                <Badge variant="outline" className="text-xs">
                                  {stock.symbol}
                                </Badge>
                              </div>
                              <p className="text-sm text-muted-foreground mt-1">
                                {stock.description}
                              </p>
                              <div className="flex items-center gap-4 mt-2 text-xs text-muted-foreground">
                                <span>현재가: ${stock.currentPrice?.toLocaleString() || 'N/A'}</span>
                                <span>시가총액: {stock.marketCap || 'N/A'}</span>
                                <span>섹터: {stock.sector || 'N/A'}</span>
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>
                    ))
                  ) : !isSearching && searchTerm.trim() !== "" ? (
                    <div className="text-center py-8 text-muted-foreground">
                      <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                      <p>검색 결과가 없습니다</p>
                      <p className="text-xs">Try different keywords (English only)</p>
                    </div>
                  ) : null}
                </div>
              )}

              {/* Initial State - Show when no search term or when searching but no results yet */}
              {(!searchTerm || (isSearching && searchResults.length === 0)) && (
                <div className="text-center py-8 text-muted-foreground">
                  <Search className="w-8 h-8 mx-auto mb-2 opacity-50" />
                  <p>기업명을 입력하여 검색하세요 (영어로 입력해주세요)</p>
                  <p className="text-xs">예: Nvidia, Tesla, Apple</p>
                </div>
              )}


            </div>

            {/* Add Button - Show when stock is selected */}
            {selectedStock && (
              <motion.div
                initial={{ opacity: 0, y: 20 }}
                animate={{ opacity: 1, y: 0 }}
                className="flex gap-3 mt-6"
              >
                <Button
                  variant="outline"
                  onClick={onClose}
                  className="flex-1 text-foreground"
                >
                  취소
                </Button>
                <Button
                  onClick={handleAddStrategy}
                  className="flex-1 bg-blue-600 hover:bg-blue-700"
                >
                  기업 추가하기
                </Button>
              </motion.div>
            )}
          </motion.div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}

// 디바운스 유틸리티 함수
function debounce<T extends (...args: any[]) => any>(
  func: T,
  wait: number
): (...args: Parameters<T>) => void {
  let timeout: NodeJS.Timeout;
  return (...args: Parameters<T>) => {
    clearTimeout(timeout);
    timeout = setTimeout(() => func(...args), wait);
  };
} 