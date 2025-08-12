"use client";

import React, { useEffect, useRef, useState } from "react";
import { ROUTE_PROGRESS_EVENTS } from "@/lib/route-progress";

export function RouteProgressBar() {
  const [visible, setVisible] = useState(false);
  const [width, setWidth] = useState(0);
  const rafRef = useRef<number | null>(null);

  useEffect(() => {
    const tick = () => {
      setWidth((prev) => {
        // Ease to 80%, then wait for complete
        const next = prev + (prev < 80 ? 0.8 + (80 - prev) * 0.02 : 0.2);
        return Math.min(next, 95);
      });
      rafRef.current = requestAnimationFrame(tick);
    };

    const handleStart = () => {
      setVisible(true);
      setWidth(5);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      rafRef.current = requestAnimationFrame(tick);
    };

    const handleEnd = () => {
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
      setWidth(100);
      // small delay for smoothness
      setTimeout(() => {
        setVisible(false);
        setWidth(0);
      }, 200);
    };

    window.addEventListener(ROUTE_PROGRESS_EVENTS.START_EVENT, handleStart as EventListener);
    window.addEventListener(ROUTE_PROGRESS_EVENTS.END_EVENT, handleEnd as EventListener);
    return () => {
      window.removeEventListener(ROUTE_PROGRESS_EVENTS.START_EVENT, handleStart as EventListener);
      window.removeEventListener(ROUTE_PROGRESS_EVENTS.END_EVENT, handleEnd as EventListener);
      if (rafRef.current) cancelAnimationFrame(rafRef.current);
    };
  }, []);

  return (
    <div className="fixed top-0 left-0 right-0 z-[100] pointer-events-none">
      <div
        className={`h-[3px] transition-opacity duration-150 ${visible ? "opacity-100" : "opacity-0"}`}
        style={{
          width: `${width}%`,
          background: "linear-gradient(90deg, #667eea, #764ba2)",
        }}
      />
    </div>
  );
}


