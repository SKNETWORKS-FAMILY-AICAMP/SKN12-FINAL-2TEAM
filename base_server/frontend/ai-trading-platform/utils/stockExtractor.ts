// AI 메시지에서 종목 심볼을 추출하는 유틸리티

// 주요 종목 심볼 매핑
const STOCK_SYMBOLS: Record<string, string> = {
  // 미국 주식
  '애플': 'NASDAQ:AAPL',
  'apple': 'NASDAQ:AAPL',
  'aapl': 'NASDAQ:AAPL',
  '마이크로소프트': 'NASDAQ:MSFT',
  'microsoft': 'NASDAQ:MSFT',
  'msft': 'NASDAQ:MSFT',
  '구글': 'NASDAQ:GOOGL',
  'google': 'NASDAQ:GOOGL',
  'googl': 'NASDAQ:GOOGL',
  '테슬라': 'NASDAQ:TSLA',
  'tesla': 'NASDAQ:TSLA',
  'tsla': 'NASDAQ:TSLA',
  '엔비디아': 'NASDAQ:NVDA',
  'nvidia': 'NASDAQ:NVDA',
  'nvda': 'NASDAQ:NVDA',
  '아마존': 'NASDAQ:AMZN',
  'amazon': 'NASDAQ:AMZN',
  'amzn': 'NASDAQ:AMZN',
  '메타': 'NASDAQ:META',
  'meta': 'NASDAQ:META',
  '페이스북': 'NASDAQ:META',
  'facebook': 'NASDAQ:META',
  '넷플릭스': 'NASDAQ:NFLX',
  'netflix': 'NASDAQ:NFLX',
  'nflx': 'NASDAQ:NFLX',
  '스팟파이': 'NYSE:SPOT',
  'spotify': 'NYSE:SPOT',
  'spot': 'NYSE:SPOT',
  
  // 한국 주식
  '삼성전자': 'KRX:005930',
  'samsung': 'KRX:005930',
  '005930': 'KRX:005930',
  'sk하이닉스': 'KRX:000660',
  'skhynix': 'KRX:000660',
  '000660': 'KRX:000660',
  'lg에너지솔루션': 'KRX:373220',
  'lg에너지': 'KRX:373220',
  '373220': 'KRX:373220',
  '현대차': 'KRX:005380',
  'hyundai': 'KRX:005380',
  '005380': 'KRX:005380',
  '기아': 'KRX:000270',
  'kia': 'KRX:000270',
  '000270': 'KRX:000270',
  'naver': 'KRX:035420',
  '035420': 'KRX:035420',
  '카카오': 'KRX:035720',
  'kakao': 'KRX:035720',
  '035720': 'KRX:035720',
  
  // ETF
  'qqq': 'NASDAQ:QQQ',
  'spy': 'NYSE:SPY',
  'voo': 'NYSE:VOO',
  'tqqq': 'NASDAQ:TQQQ',
  'soxl': 'NASDAQ:SOXL',
  
  // 일본 주식
  '토요타': 'TSE:7203',
  'toyota': 'TSE:7203',
  '7203': 'TSE:7203',
  '소니': 'TSE:6758',
  'sony': 'TSE:6758',
  '6758': 'TSE:6758',
  
  // 중국 주식
  '알리바바': 'NYSE:BABA',
  'alibaba': 'NYSE:BABA',
  'baba': 'NYSE:BABA',
  '텐센트': 'HKG:0700',
  'tencent': 'HKG:0700',
  '0700': 'HKG:0700',
};

// 정규식 패턴으로 종목 심볼 추출
const SYMBOL_PATTERNS = [
  // NASDAQ:SYMBOL 형식
  /\bNASDAQ:([A-Z]{1,5})\b/gi,
  // NYSE:SYMBOL 형식
  /\bNYSE:([A-Z]{1,5})\b/gi,
  // KRX:SYMBOL 형식
  /\bKRX:(\d{6})\b/gi,
  // TSE:SYMBOL 형식
  /\bTSE:(\d{4})\b/gi,
  // HKG:SYMBOL 형식
  /\bHKG:(\d{4})\b/gi,
  // 단독 심볼 (NASDAQ 가정)
  /\b([A-Z]{1,5})\b/gi,
];

export interface ExtractedStock {
  symbol: string;
  originalText: string;
  confidence: number;
}

/**
 * AI 메시지에서 종목 심볼을 추출합니다.
 */
export function extractStocksFromMessage(message: string): ExtractedStock[] {
  const stocks: ExtractedStock[] = [];
  const lowerMessage = message.toLowerCase();
  
  // 1. 매핑된 종목명으로 검색
  for (const [name, symbol] of Object.entries(STOCK_SYMBOLS)) {
    if (lowerMessage.includes(name.toLowerCase())) {
      stocks.push({
        symbol,
        originalText: name,
        confidence: 0.9
      });
    }
  }
  
  // 2. 정규식 패턴으로 검색
  for (const pattern of SYMBOL_PATTERNS) {
    const matches = message.matchAll(pattern);
    for (const match of matches) {
      const fullMatch = match[0];
      const symbol = match[1];
      
      // 이미 추가된 심볼인지 확인
      if (!stocks.some(s => s.symbol === fullMatch)) {
        stocks.push({
          symbol: fullMatch,
          originalText: fullMatch,
          confidence: 0.8
        });
      }
    }
  }
  
  // 3. 중복 제거 및 정렬 (신뢰도 순)
  const uniqueStocks = stocks.filter((stock, index, self) => 
    index === self.findIndex(s => s.symbol === stock.symbol)
  );
  
  return uniqueStocks.sort((a, b) => b.confidence - a.confidence);
}

/**
 * 메시지가 주식 관련인지 판단합니다.
 */
export function isStockRelatedMessage(message: string): boolean {
  const stockKeywords = [
    '주식', '주가', '투자', '매수', '매도', '차트', '기술적', '기본적',
    'stock', 'price', 'chart', 'invest', 'buy', 'sell', 'technical',
    '분석', '전망', '예측', '상승', '하락', '돌파', '지지', '저항'
  ];
  
  const lowerMessage = message.toLowerCase();
  return stockKeywords.some(keyword => lowerMessage.includes(keyword));
}

/**
 * 추출된 종목들을 기반으로 TradingView 위젯 타입을 결정합니다.
 */
export function getWidgetType(stocks: ExtractedStock[], message: string): 'mini' | 'advanced' | null {
  if (stocks.length === 0) return null;
  
  // 고급 차트가 필요한 키워드들
  const advancedKeywords = [
    '기술적 분석', '차트 분석', '지표', '인디케이터', 'RSI', 'MACD', '볼린저',
    'technical analysis', 'chart analysis', 'indicator', 'bollinger',
    '이동평균', 'moving average', '지지선', '저항선', 'support', 'resistance'
  ];
  
  const lowerMessage = message.toLowerCase();
  const needsAdvanced = advancedKeywords.some(keyword => lowerMessage.includes(keyword));
  
  return needsAdvanced ? 'advanced' : 'mini';
}
