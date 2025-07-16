"use client"

import { Card, CardContent } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TrendingUp } from "lucide-react"
import type { CSSProperties } from "react"
import { useEffect, useRef, useState } from "react"

interface StatsCardProps {
  title: string
  subtitle?: string
  value: string
  change: string
  className?: string
  style?: CSSProperties
}

export function StatsCard({ title, subtitle, value, change, className = "", style }: StatsCardProps) {
  const isPositive = change.startsWith("+")

  // 숫자 카운트업 애니메이션
  const [displayValue, setDisplayValue] = useState(value)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    // value가 숫자(혹은 $/%) 포함)일 때만 카운트업
    const numericValue = parseFloat(value.replace(/[$,%]/g, ""))
    if (isNaN(numericValue)) {
      setDisplayValue(value)
      return
    }
    let currentValue = 0
    const totalFrames = 94 // 16ms * 94 ≈ 1.5초
    const increment = numericValue / totalFrames
    let frame = 0
    const isDollar = value.includes("$")
    const isPercent = value.includes("%")
    const timer = setInterval(() => {
      frame++
      currentValue += increment
      if (currentValue >= numericValue || frame > totalFrames) {
        setDisplayValue(value)
        clearInterval(timer)
      } else {
        let formatted = Math.floor(currentValue).toLocaleString()
        if (isDollar) formatted = "$" + formatted
        if (isPercent) formatted += "%"
        setDisplayValue(formatted)
      }
    }, 16)
    return () => clearInterval(timer)
  }, [value])

  return (
    <Card
      className={`border-0 bg-[rgba(255,255,255,0.10)] dark:bg-[rgba(30,22,54,0.90)] backdrop-blur-[10px] border border-[rgba(255,255,255,0.2)] rounded-2xl p-6 shadow-[0_8px_32px_rgba(0,0,0,0.1)] transition-all duration-300 hover:scale-105 hover:shadow-[0_20px_60px_rgba(0,0,0,0.2)] ${className}`}
      style={style}
    >
      <CardContent className="p-0">
        <div className="space-y-3">
          <div>
            <h3 className="text-base font-medium text-white/80 mb-2">{title}</h3>
            {subtitle && <p className="text-xs text-white/60 mb-2">{subtitle}</p>}
          </div>
          <div className="space-y-2">
            <div ref={ref} className="text-3xl font-extrabold text-white mb-2 drop-shadow">
              {displayValue}
            </div>
            <span
              className={`inline-flex items-center px-3 py-1 rounded-full text-xs font-semibold ${
                isPositive
                  ? "bg-gradient-to-r from-teal-400 to-green-500 text-white shadow-[0_4px_15px_rgba(78,205,196,0.3)]"
                  : "bg-gradient-to-r from-red-400 to-pink-500 text-white"
              } animate-glow`}
            >
              <TrendingUp className={`w-3 h-3 mr-1 ${isPositive ? "" : "rotate-180"}`} />
              {change}
            </span>
          </div>
        </div>
      </CardContent>
      <style jsx>{`
        .animate-glow {
          animation: glow 2s ease-in-out infinite alternate;
        }
        @keyframes glow {
          from { box-shadow: 0 4px 15px rgba(78,205,196,0.3); }
          to { box-shadow: 0 4px 25px rgba(78,205,196,0.5); }
        }
      `}</style>
    </Card>
  )
}
