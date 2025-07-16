import { createSlice, createAsyncThunk, type PayloadAction } from "@reduxjs/toolkit"

interface Position {
  id: string
  symbol: string
  name: string
  quantity: number
  averagePrice: number
  currentPrice: number
  totalValue: number
  unrealizedPnL: number
  unrealizedPnLPercent: number
  sector: string
  purchaseDate: string
}

interface Transaction {
  id: string
  type: "buy" | "sell"
  symbol: string
  quantity: number
  price: number
  totalAmount: number
  fee: number
  date: string
  status: "completed" | "pending" | "cancelled"
}

interface PortfolioPerformance {
  totalValue: number
  totalCost: number
  totalPnL: number
  totalPnLPercent: number
  dayPnL: number
  dayPnLPercent: number
  cashBalance: number
}

interface PortfolioState {
  positions: Position[]
  transactions: Transaction[]
  performance: PortfolioPerformance
  isLoading: boolean
  error: string | null
  lastUpdated: number | null
}

const initialState: PortfolioState = {
  positions: [
    {
      id: "1",
      symbol: "005930",
      name: "삼성전자",
      quantity: 50,
      averagePrice: 65000,
      currentPrice: 68500,
      totalValue: 3425000,
      unrealizedPnL: 175000,
      unrealizedPnLPercent: 5.38,
      sector: "기술",
      purchaseDate: "2024-01-15",
    },
    {
      id: "2",
      symbol: "000660",
      name: "SK하이닉스",
      quantity: 30,
      averagePrice: 120000,
      currentPrice: 115000,
      totalValue: 3450000,
      unrealizedPnL: -150000,
      unrealizedPnLPercent: -4.17,
      sector: "반도체",
      purchaseDate: "2024-02-01",
    },
    {
      id: "3",
      symbol: "035420",
      name: "NAVER",
      quantity: 20,
      averagePrice: 180000,
      currentPrice: 185000,
      totalValue: 3700000,
      unrealizedPnL: 100000,
      unrealizedPnLPercent: 2.78,
      sector: "인터넷",
      purchaseDate: "2024-01-20",
    },
  ],
  transactions: [
    {
      id: "1",
      type: "buy",
      symbol: "005930",
      quantity: 50,
      price: 65000,
      totalAmount: 3250000,
      fee: 3250,
      date: "2024-01-15",
      status: "completed",
    },
    {
      id: "2",
      type: "buy",
      symbol: "000660",
      quantity: 30,
      price: 120000,
      totalAmount: 3600000,
      fee: 3600,
      date: "2024-02-01",
      status: "completed",
    },
  ],
  performance: {
    totalValue: 12575000,
    totalCost: 12000000,
    totalPnL: 575000,
    totalPnLPercent: 4.79,
    dayPnL: 125000,
    dayPnLPercent: 1.0,
    cashBalance: 2500000,
  },
  isLoading: false,
  error: null,
  lastUpdated: Date.now(),
}

export const fetchPortfolio = createAsyncThunk("portfolio/fetchPortfolio", async () => {
  // Simulate API call
  await new Promise((resolve) => setTimeout(resolve, 1000))

  return {
    positions: initialState.positions,
    performance: initialState.performance,
    timestamp: Date.now(),
  }
})

export const executeTransaction = createAsyncThunk(
  "portfolio/executeTransaction",
  async (transaction: Omit<Transaction, "id" | "status" | "date">) => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1500))

    const newTransaction: Transaction = {
      ...transaction,
      id: Date.now().toString(),
      status: "completed",
      date: new Date().toISOString().split("T")[0],
    }

    return newTransaction
  },
)

export const portfolioSlice = createSlice({
  name: "portfolio",
  initialState,
  reducers: {
    updatePositions: (state, action: PayloadAction<Position[]>) => {
      state.positions = action.payload
      state.lastUpdated = Date.now()
    },
    updatePerformance: (state, action: PayloadAction<PortfolioPerformance>) => {
      state.performance = action.payload
      state.lastUpdated = Date.now()
    },
    addTransaction: (state, action: PayloadAction<Transaction>) => {
      state.transactions.unshift(action.payload)
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchPortfolio.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchPortfolio.fulfilled, (state, action) => {
        state.isLoading = false
        state.positions = action.payload.positions
        state.performance = action.payload.performance
        state.lastUpdated = action.payload.timestamp
      })
      .addCase(fetchPortfolio.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || "포트폴리오 데이터를 가져오는데 실패했습니다"
      })
      .addCase(executeTransaction.pending, (state) => {
        state.isLoading = true
      })
      .addCase(executeTransaction.fulfilled, (state, action) => {
        state.isLoading = false
        state.transactions.unshift(action.payload)
      })
      .addCase(executeTransaction.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || "거래 실행에 실패했습니다"
      })
  },
})

export const { updatePositions, updatePerformance, addTransaction, clearError } = portfolioSlice.actions
