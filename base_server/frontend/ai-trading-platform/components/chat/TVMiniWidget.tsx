"use client";
import { useEffect, useRef } from "react";

// EXCHANGE:SYMBOL 형식 권장 (예: "NASDAQ:QQQ", "NASDAQ:AAPL")
function sanitizeSymbol(sym: string) {
  const s = sym.trim().toUpperCase();
  // 간단 방어: 허용 문자만
  if (!/^[A-Z0-9:.\-_/]{1,32}$/.test(s)) return "NASDAQ:QQQ";
  // 콜론이 없으면 나스닥 기본 가정
  return s.includes(":") ? s : `NASDAQ:${s}`;
}

export default function TVMiniWidget({
  symbol = "NASDAQ:QQQ",
  theme = "dark",         // "light" | "dark"
  dateRange = "6M",       // "1D" | "5D" | "1M" | "3M" | "6M" | "YTD" | "1Y" | "5Y" | "ALL"
  locale = "en",
}: {
  symbol?: string;
  theme?: "light" | "dark";
  dateRange?: string;
  locale?: string;
}) {
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const box = boxRef.current;
    if (!box) return;

    // 중복 임베드 방지
    box.innerHTML = "";

    const script = document.createElement("script");
    script.src =
      "https://s3.tradingview.com/external-embedding/embed-widget-mini-symbol-overview.js";
    script.async = true;

    const config = {
      symbol: sanitizeSymbol(symbol),
      width: "100%",
      height: "100%",
      locale,
      dateRange,
      colorTheme: theme,
      isTransparent: true,
      autosize: true,
    };
    script.innerHTML = JSON.stringify(config);
    box.appendChild(script);

    return () => {
      box.innerHTML = "";
    };
  }, [symbol, theme, dateRange, locale]);

  return (
    <div
      className="tradingview-widget-container"
      ref={boxRef}
      style={{ width: "100%", height: 200, minHeight: "200px" }}
    />
  );
}
