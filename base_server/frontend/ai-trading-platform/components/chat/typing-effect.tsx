"use client";

import React, { useState, useEffect } from "react";
import DOMPurify from "dompurify";

interface TypingEffectProps {
  text: string;
  onComplete?: () => void;
  onUpdate?: (currentText: string) => void;
}

export default function TypingEffect({ text, onComplete, onUpdate }: TypingEffectProps) {
  const paragraphs = text.split(/\n\s*\n/).filter((p) => p.trim().length > 0);
  const [visibleCount, setVisibleCount] = useState(0);

  useEffect(() => {
    setVisibleCount(0);
    if (paragraphs.length === 0) {
      onComplete?.();
      return;
    }
    let idx = 0;
    const showNext = () => {
      setVisibleCount((v) => v + 1);
      onUpdate?.(paragraphs.slice(0, idx + 1).join('\n\n'));
      idx++;
      if (idx < paragraphs.length) {
        setTimeout(showNext, 400);
      } else {
        setTimeout(() => onComplete?.(), 300);
      }
    };
    setTimeout(showNext, 100);
    // eslint-disable-next-line
  }, [text]);

  return (
    <div className="w-full py-8 border-b border-gray-800">
      <div className="max-w-4xl mx-auto px-4">
        {paragraphs.slice(0, visibleCount).map((p, i) => (
          <FadeInParagraph key={i}>{p}</FadeInParagraph>
        ))}
        {visibleCount < paragraphs.length && (
          <div className="flex items-center gap-2 mt-2">
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse"></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.1s' }}></div>
            <div className="w-2 h-2 bg-blue-500 rounded-full animate-pulse" style={{ animationDelay: '0.2s' }}></div>
          </div>
        )}
      </div>
    </div>
  );
}

function FadeInParagraph({ children }: { children: string }) {
  const [opacity, setOpacity] = useState(0);
  useEffect(() => {
    const t = setTimeout(() => setOpacity(1), 10);
    return () => clearTimeout(t);
  }, []);
  return (
    <div
      className="transition-all duration-500 ease-out mb-6 text-gray-100 text-base leading-relaxed prose prose-invert max-w-none"
      style={{
        opacity,
        transform: `translateY(${opacity === 0 ? '10px' : '0px'})`,
      }}
      dangerouslySetInnerHTML={{ __html: DOMPurify.sanitize(children) }}
    />
  );
} 