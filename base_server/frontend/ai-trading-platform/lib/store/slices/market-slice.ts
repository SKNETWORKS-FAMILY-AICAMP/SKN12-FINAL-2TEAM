import { createSlice, createAsyncThunk, type PayloadAction } from "@reduxjs/toolkit"

interface MarketData {
  symbol: string
  name: string
  price: number
  change: number
  changePercent: number
  volume: string
  marketCap?: string
  high52Week?: number
  low52Week?: number
  timestamp: number
}

interface MarketNews {
  id: string
  title: string
  summary: string
  source: string
  publishedAt: string
  sentiment: "positive" | "negative" | "neutral"
  impact: "high" | "medium" | "low"
}

interface MarketState {
  indices: MarketData[]
  stocks: MarketData[]
  news: MarketNews[]
  isLoading: boolean
  error: string | null
  lastUpdated: number | null
  marketStatus: "open" | "closed" | "pre_market" | "after_hours"
}

const initialState: MarketState = {
  indices: [
    {
      symbol: "KOSPI",
      name: "코스피",
      price: 2485.67,
      change: 12.34,
      changePercent: 0.5,
      volume: "₩8.2조",
      timestamp: Date.now(),
    },
    {
      symbol: "KOSDAQ",
      name: "코스닥",
      price: 845.23,
      change: -5.67,
      changePercent: -0.67,
      volume: "₩3.1조",
      timestamp: Date.now(),
    },
    {
      symbol: "S&P500",
      name: "S&P 500",
      price: 4567.89,
      change: 23.45,
      changePercent: 0.52,
      volume: "$142B",
      timestamp: Date.now(),
    },
    {
      symbol: "NASDAQ",
      name: "나스닥",
      price: 14234.56,
      change: 45.67,
      changePercent: 0.32,
      volume: "$89B",
      timestamp: Date.now(),
    },
  ],
  stocks: [],
  news: [
    {
      id: "1",
      title: "기술주 강세 지속, AI 관련주 급등",
      summary: "인공지능 관련 기업들의 실적 개선 기대감으로 기술주가 강세를 보이고 있습니다.",
      source: "한국경제",
      publishedAt: "2시간 전",
      sentiment: "positive",
      impact: "high",
    },
    {
      id: "2",
      title: "연준 금리 동결 전망 강화",
      summary: "최근 경제 지표를 바탕으로 연준이 금리를 동결할 가능성이 높아졌습니다.",
      source: "매일경제",
      publishedAt: "4시간 전",
      sentiment: "neutral",
      impact: "medium",
    },
  ],
  isLoading: false,
  error: null,
  lastUpdated: Date.now(),
  marketStatus: "open",
}

export const fetchMarketData = createAsyncThunk("market/fetchMarketData", async () => {
  // Simulate API call
  await new Promise((resolve) => setTimeout(resolve, 1000))

  return {
    indices: initialState.indices.map((index) => ({
      ...index,
      price: index.price + (Math.random() - 0.5) * 10,
      change: (Math.random() - 0.5) * 20,
      changePercent: (Math.random() - 0.5) * 2,
      timestamp: Date.now(),
    })),
    timestamp: Date.now(),
  }
})

export const fetchMarketNews = createAsyncThunk("market/fetchMarketNews", async () => {
  // Simulate API call
  await new Promise((resolve) => setTimeout(resolve, 800))

  return initialState.news
})

export const marketSlice = createSlice({
  name: "market",
  initialState,
  reducers: {
    updateMarketData: (state, action: PayloadAction<MarketData[]>) => {
      state.indices = action.payload
      state.lastUpdated = Date.now()
    },
    setMarketStatus: (state, action: PayloadAction<MarketState["marketStatus"]>) => {
      state.marketStatus = action.payload
    },
    addStock: (state, action: PayloadAction<MarketData>) => {
      const existingIndex = state.stocks.findIndex((stock) => stock.symbol === action.payload.symbol)
      if (existingIndex >= 0) {
        state.stocks[existingIndex] = action.payload
      } else {
        state.stocks.push(action.payload)
      }
    },
    removeStock: (state, action: PayloadAction<string>) => {
      state.stocks = state.stocks.filter((stock) => stock.symbol !== action.payload)
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchMarketData.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchMarketData.fulfilled, (state, action) => {
        state.isLoading = false
        state.indices = action.payload.indices
        state.lastUpdated = action.payload.timestamp
      })
      .addCase(fetchMarketData.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || "시장 데이터를 가져오는데 실패했습니다"
      })
      .addCase(fetchMarketNews.pending, (state) => {
        state.isLoading = true
      })
      .addCase(fetchMarketNews.fulfilled, (state, action) => {
        state.isLoading = false
        state.news = action.payload
      })
      .addCase(fetchMarketNews.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || "뉴스를 가져오는데 실패했습니다"
      })
  },
})

export const { updateMarketData, setMarketStatus, addStock, removeStock, clearError } = marketSlice.actions
