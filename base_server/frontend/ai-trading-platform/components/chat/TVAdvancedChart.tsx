"use client";
import { useEffect, useRef } from "react";

function sanitizeSymbol(sym: string) {
  const s = sym.trim().toUpperCase();
  return /^[A-Z0-9:.\-_/]{1,32}$/.test(s) ? (s.includes(":") ? s : `NASDAQ:${s}`) : "NASDAQ:QQQ";
}

export default function TVAdvancedChart({
  symbol = "NASDAQ:QQQ",
  theme = "dark",    // "light" | "dark"
  interval = "D",    // "1" "5" "15" "60" "D" "W" "M"
  locale = "en",
  timezone = "Asia/Seoul",
}: {
  symbol?: string;
  theme?: "light" | "dark";
  interval?: string;
  locale?: string;
  timezone?: string;
}) {
  const boxRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const box = boxRef.current;
    if (!box) return;
    box.innerHTML = "";

    const script = document.createElement("script");
    script.src =
      "https://s3.tradingview.com/external-embedding/embed-widget-advanced-chart.js";
    script.async = true;

    const config = {
      autosize: true,
      symbol: sanitizeSymbol(symbol),
      interval,
      timezone,
      theme,
      style: "1",
      locale,
      hide_top_toolbar: false,
      hide_legend: false,
      allow_symbol_change: true,
      withdateranges: true,
      calendar: false,
      // studies: ["RSI@tv-basicstudies"], // 필요 시 인디케이터
      support_host: "https://www.tradingview.com",
    };

    script.innerHTML = JSON.stringify(config);
    box.appendChild(script);

    return () => {
      box.innerHTML = "";
    };
  }, [symbol, theme, interval, locale, timezone]);

  return (
    <div
      className="tradingview-widget-container"
      style={{ width: "100%", height: 300, minHeight: "300px" }}
      ref={boxRef}
    />
  );
}
