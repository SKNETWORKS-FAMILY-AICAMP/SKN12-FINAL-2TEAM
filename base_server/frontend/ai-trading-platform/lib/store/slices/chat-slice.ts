import { createSlice, createAsyncThunk, type PayloadAction } from "@reduxjs/toolkit"

interface ChatMessage {
  id: string
  content: string
  role: "user" | "assistant"
  timestamp: number
  metadata?: {
    tool?: string
    confidence?: number
    sources?: string[]
  }
}

interface ChatConversation {
  id: string
  title: string
  messages: ChatMessage[]
  createdAt: number
  updatedAt: number
}

interface AITool {
  id: string
  name: string
  description: string
  category: "analysis" | "trading" | "research" | "portfolio"
  isActive: boolean
  icon: string
}

interface ChatState {
  conversations: ChatConversation[]
  currentConversationId: string | null
  availableTools: AITool[]
  selectedTool: string | null
  isLoading: boolean
  isStreaming: boolean
  error: string | null
}

const initialState: ChatState = {
  conversations: [
    {
      id: "1",
      title: "시장 분석 문의",
      messages: [
        {
          id: "1",
          content: "안녕하세요! AI 트레이딩 어드바이저입니다. 어떤 도움이 필요하신가요?",
          role: "assistant",
          timestamp: Date.now() - 3600000,
        },
      ],
      createdAt: Date.now() - 3600000,
      updatedAt: Date.now() - 3600000,
    },
  ],
  currentConversationId: "1",
  availableTools: [
    {
      id: "market_analysis",
      name: "시장 분석",
      description: "실시간 시장 데이터 분석 및 트렌드 예측",
      category: "analysis",
      isActive: true,
      icon: "TrendingUp",
    },
    {
      id: "stock_screener",
      name: "종목 스크리너",
      description: "조건에 맞는 종목 검색 및 필터링",
      category: "research",
      isActive: true,
      icon: "Search",
    },
    {
      id: "portfolio_optimizer",
      name: "포트폴리오 최적화",
      description: "리스크 대비 수익률 최적화 분석",
      category: "portfolio",
      isActive: true,
      icon: "Target",
    },
    {
      id: "trading_signals",
      name: "트레이딩 시그널",
      description: "AI 기반 매매 신호 생성",
      category: "trading",
      isActive: true,
      icon: "Zap",
    },
  ],
  selectedTool: null,
  isLoading: false,
  isStreaming: false,
  error: null,
}

export const sendMessage = createAsyncThunk(
  "chat/sendMessage",
  async ({ content, tool }: { content: string; tool?: string }) => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))

    const userMessage: ChatMessage = {
      id: Date.now().toString(),
      content,
      role: "user",
      timestamp: Date.now(),
      metadata: tool ? { tool } : undefined,
    }

    // Simulate AI response
    const aiResponse: ChatMessage = {
      id: (Date.now() + 1).toString(),
      content: `${content}에 대한 분석 결과입니다. AI 모델을 통해 분석한 결과, 현재 시장 상황을 고려할 때 다음과 같은 인사이트를 제공할 수 있습니다.`,
      role: "assistant",
      timestamp: Date.now() + 1000,
      metadata: {
        tool,
        confidence: Math.floor(Math.random() * 30) + 70,
        sources: ["시장 데이터", "기술적 분석", "펀더멘털 분석"],
      },
    }

    return { userMessage, aiResponse }
  },
)

export const createConversation = createAsyncThunk("chat/createConversation", async (title: string) => {
  const newConversation: ChatConversation = {
    id: Date.now().toString(),
    title,
    messages: [
      {
        id: Date.now().toString(),
        content: "새로운 대화를 시작합니다. 무엇을 도와드릴까요?",
        role: "assistant",
        timestamp: Date.now(),
      },
    ],
    createdAt: Date.now(),
    updatedAt: Date.now(),
  }

  return newConversation
})

export const chatSlice = createSlice({
  name: "chat",
  initialState,
  reducers: {
    setCurrentConversation: (state, action: PayloadAction<string>) => {
      state.currentConversationId = action.payload
    },
    setSelectedTool: (state, action: PayloadAction<string | null>) => {
      state.selectedTool = action.payload
    },
    toggleTool: (state, action: PayloadAction<string>) => {
      const tool = state.availableTools.find((t) => t.id === action.payload)
      if (tool) {
        tool.isActive = !tool.isActive
      }
    },
    clearError: (state) => {
      state.error = null
    },
    setStreaming: (state, action: PayloadAction<boolean>) => {
      state.isStreaming = action.payload
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(sendMessage.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(sendMessage.fulfilled, (state, action) => {
        state.isLoading = false
        const currentConversation = state.conversations.find((c) => c.id === state.currentConversationId)
        if (currentConversation) {
          currentConversation.messages.push(action.payload.userMessage)
          currentConversation.messages.push(action.payload.aiResponse)
          currentConversation.updatedAt = Date.now()
        }
      })
      .addCase(sendMessage.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || "메시지 전송에 실패했습니다"
      })
      .addCase(createConversation.fulfilled, (state, action) => {
        state.conversations.unshift(action.payload)
        state.currentConversationId = action.payload.id
      })
  },
})

export const { setCurrentConversation, setSelectedTool, toggleTool, clearError, setStreaming } = chatSlice.actions
