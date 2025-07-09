export interface Stock {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: number
  marketCap?: number
  pe?: number
  pb?: number
  roe?: number
}

export interface Portfolio {
  id: string
  stocks: PortfolioStock[]
  totalValue: number
  totalReturn: number
  totalReturnPercent: number
  cash: number
}

export interface PortfolioStock {
  symbol: string
  name: string
  shares: number
  avgPrice: number
  currentPrice: number
  totalValue: number
  return: number
  returnPercent: number
}

export interface ChatMessage {
  id: string
  type: "user" | "ai"
  content: string
  timestamp: Date
  isTyping?: boolean
}

export interface User {
  id: string
  name: string
  email: string
  subscriptionTier: "Standard" | "PRO" | "EXPERT"
  investmentExperience: "Beginner" | "Intermediate" | "Advanced"
  riskTolerance: "Conservative" | "Moderate" | "Aggressive"
  investmentGoals: string[]
}

export interface MarketAlert {
  id: string
  type: "surge" | "crash" | "news" | "target"
  title: string
  message: string
  timestamp: Date
  severity: "low" | "medium" | "high"
}
