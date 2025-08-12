import { useState, useEffect, useRef, useCallback } from "react";

// -------------------------
// StockInfo 구조
// -------------------------
export class StockInfo {
  constructor(
    public symbol: string,
    public price: number,
    public change: number,
    public changePct: number,
    public volume: number,
    public timestamp: string
  ) {}
}

// -------------------------
// OAuth 인증 함수
// -------------------------
async function fetchApiKeys(): Promise<{ appkey: string; appsecret: string } | null> {
  try {
    const res = await fetch("/api/account/api-keys?key=access_db_key", { credentials: "include" });
    if (!res.ok) throw new Error("API 키 요청 실패");
    const data = await res.json();
    return { appkey: data.korea_investment_app_key, appsecret: data.korea_investment_app_secret };
  } catch (err) {
    console.warn("API 키 로드 실패:", err);
    return null;
  }
}

async function getOAuthToken(appkey: string, appsecret: string): Promise<string | null> {
  try {
    const cacheKey = "nasdaq_token";
    const cacheExp = "nasdaq_token_expires";
    const cached = localStorage.getItem(cacheKey);
    const expires = Number(localStorage.getItem(cacheExp) || 0);
    if (cached && Date.now() < expires) return cached;

    const res = await fetch("https://openapi.koreainvestment.com:9443/oauth2/tokenP", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ grant_type: "client_credentials", appkey, appsecret }),
    });
    if (!res.ok) throw new Error("토큰 발급 실패");
    const data = await res.json();
    localStorage.setItem(cacheKey, data.access_token);
    localStorage.setItem(cacheExp, (Date.now() + data.expires_in * 1000 - 60000).toString());
    return data.access_token;
  } catch (err) {
    console.warn("OAuth 토큰 발급 실패:", err);
    return null;
  }
}

// -------------------------
// WebSocket 관리
// -------------------------
class NasdaqWebSocketManager {
  private ws: WebSocket | null = null;
  private token: string | null = null;
  private appkey: string | null = null;
  private subscribers = new Map<string, (data: StockInfo) => void>();

  async init() {
    const keys = await fetchApiKeys();
    if (!keys) return;
    const token = await getOAuthToken(keys.appkey, keys.appsecret);
    if (!token) return;
    this.token = token;
    this.appkey = keys.appkey;
    this.connect();
  }

  connect() {
    if (this.ws) return;
    this.ws = new WebSocket("wss://openapi.koreainvestment.com:9443/ws");

    this.ws.onopen = () => console.log("NASDAQ WebSocket 연결됨");
    this.ws.onclose = () => {
      console.warn("WebSocket 종료, 재연결 대기");
      this.ws = null;
    };
    this.ws.onmessage = (event) => {
      if (typeof event.data !== "string") return;
      const parsed = this.parseMessage(event.data);
      if (parsed && this.subscribers.has(parsed.symbol)) {
        this.subscribers.get(parsed.symbol)!(parsed);
      }
    };
  }

  parseMessage(msg: string): StockInfo | null {
    // 실제 나스닥 데이터 파싱 로직 작성 필요 (임시)
    const parts = msg.split("|");
    if (parts.length < 4) return null;
    const symbol = parts[1];
    const price = parseFloat(parts[2]);
    const change = parseFloat(parts[3]);
    return new StockInfo(symbol, price, change, (change / price) * 100, 0, new Date().toISOString());
  }

  subscribe(symbol: string, callback: (data: StockInfo) => void) {
    this.subscribers.set(symbol, callback);
    if (this.ws?.readyState === WebSocket.OPEN && this.token && this.appkey) {
      const message = JSON.stringify({
        header: { authorization: `Bearer ${this.token}`, appkey: this.appkey, tr_id: "NASD_QTES" },
        body: { input: { tr_key: symbol } },
      });
      this.ws.send(message);
    }
  }
}

// 싱글톤 매니저
let wsManager: NasdaqWebSocketManager | null = null;
function getWsManager() {
  if (!wsManager) wsManager = new NasdaqWebSocketManager();
  return wsManager;
}

// -------------------------
// REST 종가 데이터 (백업)
// -------------------------
async function fetchRestPrice(symbol: string, token: string, appkey: string): Promise<StockInfo | null> {
  try {
    const res = await fetch(`/api/nasdaq/close?symbol=${symbol}`, {
      headers: { Authorization: `Bearer ${token}`, "x-app-key": appkey },
    });
    if (!res.ok) throw new Error("REST 종가 요청 실패");
    const data = await res.json();
    return new StockInfo(
      symbol,
      data.price,
      data.change,
      data.changePct,
      data.volume || 0,
      data.timestamp || new Date().toISOString()
    );
  } catch (err) {
    console.warn("REST 종가 가져오기 실패:", err);
    return null;
  }
}

// -------------------------
// 훅: useNasdaqStocks
// -------------------------
export function useNasdaqStocks() {
  const [stockMap, setStockMap] = useState<Record<string, StockInfo>>({});
  const managerRef = useRef<NasdaqWebSocketManager>(getWsManager());
  const tokenRef = useRef<string | null>(null);
  const appkeyRef = useRef<string | null>(null);

  useEffect(() => {
    const init = async () => {
      const keys = await fetchApiKeys();
      if (!keys) return;
      const token = await getOAuthToken(keys.appkey, keys.appsecret);
      if (!token) return;
      tokenRef.current = token;
      appkeyRef.current = keys.appkey;
      await managerRef.current.init();
    };
    init();
  }, []);

  const addSymbol = useCallback(async (symbol: string) => {
    // WebSocket 구독 시도
    managerRef.current.subscribe(symbol, (data: StockInfo) => {
      setStockMap((prev) => ({ ...prev, [symbol]: data }));
    });

    // 1초 안에 값이 안오면 REST API 백업
    setTimeout(async () => {
      if (!stockMap[symbol] && tokenRef.current && appkeyRef.current) {
        const restData = await fetchRestPrice(symbol, tokenRef.current, appkeyRef.current);
        if (restData) {
          setStockMap((prev) => ({ ...prev, [symbol]: restData }));
        }
      }
    }, 1000);
  }, [stockMap]);

  const getStock = useCallback((symbol: string): StockInfo | undefined => {
    if (!stockMap[symbol]) {
      addSymbol(symbol);
      return undefined;
    }
    return stockMap[symbol];
  }, [stockMap, addSymbol]);

  return { getStock, stockMap, addSymbol };
}
