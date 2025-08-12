"use client";
import { useCallback, useRef } from "react";

/* ───────────────────────────────────────── */
/* 1) 전역 스토어                            */
/* ───────────────────────────────────────── */
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
export const StockInfoStore = new Map<string, StockInfo>();

/* ───────────────────────────────────────── */
/* 2) OAuth + REST 헬퍼                      */
/* ───────────────────────────────────────── */
let cachedToken  : string | null = null;
let cachedAppKey : string | null = null;
let cachedUntil  = 0;
let inFlight: Promise<void> | null = null;

const mask = (v?: string | null, keep = 4) =>
  !v ? "" : (v.length <= keep ? "*".repeat(v.length) : v.slice(0, keep) + "*".repeat(v.length - keep));

async function fetchOAuthCredential(): Promise<{ token: string; appkey: string } | null> {
  // ✅ SSR 가드
  if (typeof window === "undefined") {
    console.warn("[OAuth] called on server – blocked");
    return null;
  }

  // ✅ 캐시 우선
  const cacheReady = cachedToken && cachedAppKey && Date.now() < cachedUntil;
  if (cacheReady) return { token: cachedToken!, appkey: cachedAppKey! };

  // ✅ 단일 임계구역
  if (inFlight) {
    await inFlight;
    return (cachedToken && cachedAppKey && Date.now() < cachedUntil)
      ? { token: cachedToken!, appkey: cachedAppKey! }
      : null;
  }

  inFlight = (async () => {
    try {
      console.log("[OAuth] 발급 시도");
      const accessToken = localStorage.getItem("accessToken");
      if (!accessToken) throw new Error("accessToken 없음");

      const res = await fetch("/api/dashboard/oauth/authenticate", {
        headers: { Authorization: `Bearer ${accessToken}` },
      });
      console.log("[OAuth] TESWTdddddsdfga응답:", res);
      if (!res.ok) throw new Error(`HTTP ${res.status}`);

      const data = await res.json();
      console.log("[OAuth] 응답:",data,"ddddd}{", { ...data, access_token: mask(data?.access_token), app_key: mask(data?.app_key) });

      if (!data.app_key) {
        throw new Error(`업무 실패: ${data.message ?? ""}`);
      }

      // ⚠️ 서버 응답 필드명 확인 필수
      const token  = data.access_token ?? data.app_key ?? null;
      const appkey = data.app_key ?? data.appKey ?? null;
      if (!token || !appkey) throw new Error("access_token 또는 app_key 없음");

      cachedToken  = token;
      cachedAppKey = appkey;
      cachedUntil  = Date.now() + 55 * 60 * 1000; // 55분
    } catch (e) {
      console.error("[OAuth] 실패:", e);
      cachedToken = null; cachedAppKey = null; cachedUntil = 0;
    } finally {
  const p = inFlight;
  inFlight = null;
  if (p) {
    try {
      await p;
    } catch {
      /* ignore */
    }
  }
}
  })();

  await inFlight;
  return (cachedToken && cachedAppKey && Date.now() < cachedUntil)
    ? { token: cachedToken!, appkey: cachedAppKey! }
    : null;
}

async function fetchRestPrice(sym: string) {
  const userAccessToken =
    typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;

  if (!userAccessToken) {
    console.warn("[REST] 사용자 accessToken 없음 → 요청 중단");
    return;
  }

  console.log("%c[REST] 종가 요청 시작", "color:orange; font-weight:bold;", {
    symbol: sym,
    userTokenPreview: userAccessToken.slice(0, 6) + "...",
  });

  // 공통 숫자 정규화
  const toNumber = (v: unknown): number => {
    if (v === null || v === undefined) return 0;
    if (typeof v === "number") return Number.isFinite(v) ? v : 0;
    if (typeof v === "string") {
      const s = v.trim().replace(/,/g, "");
      const n = parseFloat(s);
      return Number.isFinite(n) ? n : 0;
    }
    const n = Number(v);
    return Number.isFinite(n) ? n : 0;
  };

  try {
    const reqBody: any = {
      ticker: sym,
      appkey: cachedAppKey,
      kisToken: cachedToken,
    };
    console.debug("[REST] 요청 바디:", {
      ...reqBody,
      appkey: reqBody.appkey?.slice(0, 6) + "...",
      kisToken: reqBody.kisToken?.slice(0, 6) + "...",
    });

    const res = await fetch("/api/dashboard/price/us", {
      method: "POST",
      headers: {
        Authorization: `Bearer ${userAccessToken}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify(reqBody),
    });

    console.debug("[REST] HTTP 상태코드:", res.status);
    if (!res.ok) {
      const errText = await res.text();
      console.error("[REST] HTTP 오류", { status: res.status, body: errText });
      return;
    }

    const a: any = await res.json();
    const d: any = JSON.parse(a ?? "{}");
    console.log("[REST] 응답(JSON):", d);

    // ✅ errorCode 문자열/숫자 모두 대응
    const errCode = Number(d?.errorCode ?? 0);
    if (Number.isFinite(errCode) && errCode !== 0) {
      console.error("[REST] 업무 실패", d);
      return;
    }

    // ✅ 너가 보여준 백엔드 표준 응답에 정확히 매핑
    const symbolRaw = d?.ticker ?? sym;
    const priceRaw = d?.price;
    const changeRaw = d?.change;
    const pctRaw   = d?.change_pct; // 퍼센트 값(예: -0.3 == -0.3%)
    const volRaw   = d?.volume;
    const tsVal    = d?.timestamp ?? new Date().toISOString();

    const priceNum  = toNumber(priceRaw);
    const changeNum = toNumber(changeRaw);
    const pctNum    = toNumber(pctRaw);
    const volNum    = toNumber(volRaw);

    // 재계산 함수
    const recomputePct = () => {
      const prevClose = priceNum - changeNum;
      if (!prevClose || !Number.isFinite(prevClose)) return 0;
      return (changeNum / prevClose) * 100;
    };

    // ✅ 서버 값 신뢰: 부호 불일치라도 '그대로' 사용
    let cpct: number;
    if (Number.isFinite(pctNum)) {
      const absurd = Math.abs(pctNum) > 50; // 진짜 비정상일 때만 보정
      cpct = absurd ? recomputePct() : pctNum;
    } else {
      // 서버가 pct를 안 준 경우에만 재계산
      cpct = recomputePct();
    }

    console.log(
      "%c[REST][RESULT]",
      "color:#9cf;font-weight:bold",
      {
        symbol: String(symbolRaw).toUpperCase(),
        price: priceNum,
        change: changeNum,
        change_pct: cpct,
        volume: volNum,
        timestamp: tsVal,
      }
    );

    // ✅ 스토어 반영
    const stockInfo = new StockInfo(
      String(symbolRaw).toUpperCase(),
      priceNum,
      changeNum,
      cpct,
      volNum,
      tsVal
    );
    
    console.log("%c[REST] 스토어 저장 전 데이터 검증:", "color:yellow", {
      symbol: sym,
      price: priceNum,
      change: changeNum,
      change_pct: cpct,
      volume: volNum,
      timestamp: tsVal
    });
    
    StockInfoStore.set(sym, stockInfo);
    console.log("%c[REST] 스토어 저장 완료", "color:green", sym);

    if (typeof window !== "undefined") {
      window.dispatchEvent(new CustomEvent("stock_update", { detail: sym }));
      console.log("%c[REST] stock_update 이벤트 발행", "color:cyan", sym);
    }
  } catch (e) {
    console.warn("[REST] 종가 실패:", e);
  }

  console.log("%c[REST] 종가 요청 종료", "color:orange; font-weight:bold;", sym);
}

/* ───────────────────────────────────────── */
/* 3) WebSocket 매니저                       */
/* ───────────────────────────────────────── */
class NasdaqWebSocketManager {
  private ws: WebSocket | null = null;
  private queue = new Set<string>();
  private connecting = false; // 중복 init 방지

  async init(): Promise<boolean> {
    console.log("%c[WS] init() 시작", "color:yellow");

    if (this.ws) {
      console.warn("[WS] 이미 WebSocket 연결이 존재 → init 종료");
      return true;
    }
    if (this.connecting) {
      console.log("[WS] 연결 시도 중 → init 스킵");
      return false;
    }
    this.connecting = true;

    try {
      if (inFlight) {
        console.log("[WS] inFlight 상태 감지 → 토큰 발급 완료 대기");
        await inFlight;
      }

      const ready = cachedToken && cachedAppKey && Date.now() < cachedUntil;
      console.log(
        "%c[WS] 캐시 상태:",
        "color:cyan",
        "appkey =", mask(cachedAppKey),
        "token =", mask(cachedToken),
        "until =", cachedUntil ? new Date(cachedUntil).toLocaleString() : "(none)",
        "ready =", ready ? "✅ ready" : "❌ not ready"
      );

      const cred = ready ? { token: cachedToken!, appkey: cachedAppKey! } : await fetchOAuthCredential();
      console.log("[WS] credential 선택:", { token: mask(cred?.token), appkey: mask(cred?.appkey) });

      if (!cred) {
        console.error("[WS] 인증 실패 → WS 연결 중단");
        return false;
      }

      console.log("[WS] WebSocket 연결 시도");
      this.connect(cred.token, cred.appkey);
      console.log("%c[WS] init() 종료", "color:yellow");
      return true;
    } finally {
      this.connecting = false;
    }
  }

  private connect(token: string, appkey: string) {
    console.log("%c[WS] connecting…", "color:#888");
    this.ws = new WebSocket("wss://openapi.koreainvestment.com:9443/ws");

    this.ws.onopen = () => {
      console.log("%c[WS] OPEN", "color:lime");
      this.queue.forEach((s) => this._sendSub(s, token, appkey));
      this.queue.clear();
    };

    this.ws.onmessage = (ev) => {
      const raw = ev.data as string;
      if (raw.startsWith('{"header":{"tr_id":"PINGPONG')) return; // ping

      const p = this.parseMessage(raw);
      if (!p) return;

      console.log("%c[WS] 스토어 저장 전 데이터 검증:", "color:yellow", {
        symbol: p.symbol,
        price: p.price,
        change: p.change,
        changePct: p.changePct,
        volume: p.volume,
        timestamp: p.timestamp
      });

      StockInfoStore.set(p.symbol, p);
      window.dispatchEvent(new CustomEvent("stock_update", { detail: p.symbol }));
    };

    this.ws.onclose = async (e) => {
      console.warn("[WS] CLOSE", e.code, e.reason ?? "");

      const symbols = Array.from(this.queue);
      this.queue.clear();

      // 즉시 REST 보정
      if (cachedToken && cachedAppKey && symbols.length) {
        await Promise.all([...symbols].map((sym) => fetchRestPrice(sym)));
      }

      // 장중에만 재연결(간단 버전)
      const nowET = new Date().toLocaleString("en-US", {
        timeZone: "America/New_York",
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
      });
      if (nowET >= "09:25" && nowET <= "16:10") {
        console.log("[WS] 장중 → 10초 후 재연결 시도");
        setTimeout(() => this.init(), 10_000);
      } else {
        console.log("[WS] 장마감 → 재연결 보류, REST 사용");
      }

      this.ws = null;
    };
  }

  /** 실시간 틱 문자열 → StockInfo */
  private parseMessage(raw: string): StockInfo | null {
    // 기본 가정: "SEQ|QQQ|375.12|+1.25|0.33|..." (가격|변동치|변동률)
    const parts = raw.split("|");
    if (parts.length < 5) return null;
    
    const symbol = parts[1];
    const price = Number(parts[2]);
    
    // 변동치 부호 처리 개선
    let change: number;
    const changeStr = parts[3];
    if (changeStr.startsWith('+')) {
      change = Number(changeStr.substring(1));
    } else if (changeStr.startsWith('-')) {
      change = -Number(changeStr.substring(1));
    } else {
      change = Number(changeStr);
    }
    
    // 변동률 처리 (백엔드에서 제공하는 값 사용)
    let pct: number;
    if (parts.length >= 5) {
      const pctStr = parts[4];
      if (pctStr.startsWith('+')) {
        pct = Number(pctStr.substring(1));
      } else if (pctStr.startsWith('-')) {
        pct = -Number(pctStr.substring(1));
      } else {
        pct = Number(pctStr);
      }
    } else {
      // 백엔드에서 변동률을 제공하지 않는 경우에만 계산
      pct = price ? (change / price) * 100 : 0;
    }
    
    if (!isFinite(price) || !isFinite(change) || !isFinite(pct)) return null;
    
    console.log("[WS] 메시지 파싱:", {
      raw,
      symbol,
      price,
      changeStr,
      change,
      pctStr: parts[4] || 'N/A',
      pct
    });
    
    return new StockInfo(symbol, price, change, pct, 0, new Date().toISOString());
  }

  private _sendSub(sym: string, token: string, appkey: string) {
    if (!this.ws || this.ws.readyState !== WebSocket.OPEN) {
      this.queue.add(sym);
      return;
    }
    this.ws.send(
      JSON.stringify({
        header: { authorization: `Bearer ${token}`, appkey, tr_id: "NASD_QTES" },
        body: { input: { tr_key: sym } },
      })
    );
    console.log("%c[WS] SUB ▶", "color:#ff0", sym);
  }

  subscribe(sym: string) {
    if (!cachedToken || Date.now() >= cachedUntil) {
      this.queue.add(sym);
      return;
    }
    this._sendSub(sym, cachedToken, cachedAppKey!);
  }
}

let wsMgr: NasdaqWebSocketManager | null = null;
const getWsMgr = () => (wsMgr ??= new NasdaqWebSocketManager());

/* ───────────────────────────────────────── */
/* 4) React Hook (export)                    */
/* ───────────────────────────────────────── */
export function useNasdaqStocks() {
  const mgr = useRef(getWsMgr()).current;

  const initWs = useCallback(async () => {
    const ok = await mgr.init();   // ✅ 성공/실패 boolean
    return ok;
  }, [mgr]);

  const addSymbol = useCallback((sym: string) => {
    mgr.subscribe(sym);
    // 1초 후 REST 보정
    setTimeout(() => {
      if (!StockInfoStore.has(sym)) {
        void fetchRestPrice(sym);
      }
    }, 1000);
  }, []);

  const getStock = useCallback((s: string) => StockInfoStore.get(s), []);
  const subscribeStore = useCallback((cb: () => void) => {
    const handler = () => cb();
    window.addEventListener("stock_update", handler as EventListener);
    return () => window.removeEventListener("stock_update", handler as EventListener);
  }, []);

  return { initWs, addSymbol, getStock, subscribeStore };
}
