"use client";
import React from "react";
import TickerItem from "@/components/dashboard/TickerItem";
import "@/styles/ticker.css";

const SYMBOLS_TO_SHOW = [
  "QQQ", "QQQM", "QQQJ", "ONEQ", "TQQQ", "SQQQ",
  "IBIT", "TSLL", "QYLD", "GLDI", "SLVO"
];

export default function WorldIndicesTicker() {
  return (
    <div className="bg-gray-900/80 backdrop-blur-sm border-b border-gray-700/50 shadow-lg overflow-hidden whitespace-nowrap h-10 flex items-center">
      <div className="ticker-container">
        <div className="ticker-content">
          {SYMBOLS_TO_SHOW.map((sym, idx) => (
            <TickerItem key={sym} symbol={sym} subscribeDelayMs={idx * 800} />
          ))}
        </div>
        {/* 무한 스크롤 복제 */}
        <div className="ticker-content">
          {SYMBOLS_TO_SHOW.map((sym, idx) => (
            <TickerItem key={`${sym}-dup`} symbol={sym} subscribeDelayMs={(SYMBOLS_TO_SHOW.length + idx) * 800} />
          ))}
        </div>
      </div>
    </div>
  );
}
