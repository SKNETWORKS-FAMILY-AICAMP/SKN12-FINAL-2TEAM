"use client"

import { TrendingUp, Zap } from "lucide-react"

export function Logo() {
  return (
    <div className="flex items-center gap-3">
      <div className="relative">
        <div className="w-10 h-10 bg-gradient-to-br from-blue-500 via-purple-600 to-indigo-600 rounded-xl flex items-center justify-center shadow-lg">
          <TrendingUp className="h-5 w-5 text-white" />
        </div>
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-gradient-to-br from-yellow-400 to-orange-500 rounded-full flex items-center justify-center">
          <Zap className="h-2 w-2 text-white" />
        </div>
      </div>
      <div>
        <h1 className="text-xl font-bold gradient-text">AI Trader Pro</h1>
        <p className="text-xs text-gray-500 dark:text-gray-400">Professional Trading Platform</p>
      </div>
    </div>
  )
}
