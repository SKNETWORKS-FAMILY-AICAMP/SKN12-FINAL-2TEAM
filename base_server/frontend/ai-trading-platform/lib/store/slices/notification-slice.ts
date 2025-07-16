import { createSlice, createAsyncThunk, type PayloadAction } from "@reduxjs/toolkit"

interface Notification {
  id: string
  title: string
  message: string
  type: "info" | "success" | "warning" | "error"
  category: "trading" | "market" | "portfolio" | "system" | "ai"
  isRead: boolean
  createdAt: number
  actionUrl?: string
  metadata?: {
    symbol?: string
    amount?: number
    percentage?: number
  }
}

interface NotificationSettings {
  trading: boolean
  market: boolean
  portfolio: boolean
  ai: boolean
  email: boolean
  push: boolean
  sms: boolean
}

interface NotificationState {
  notifications: Notification[]
  settings: NotificationSettings
  unreadCount: number
  isLoading: boolean
  error: string | null
}

const initialState: NotificationState = {
  notifications: [
    {
      id: "1",
      title: "매수 주문 체결",
      message: "삼성전자 50주 매수 주문이 체결되었습니다.",
      type: "success",
      category: "trading",
      isRead: false,
      createdAt: Date.now() - 600000,
      metadata: {
        symbol: "005930",
        amount: 50,
      },
    },
    {
      id: "2",
      title: "AI 매매 신호",
      message: "SK하이닉스에 대한 매도 신호가 감지되었습니다.",
      type: "warning",
      category: "ai",
      isRead: false,
      createdAt: Date.now() - 1200000,
      metadata: {
        symbol: "000660",
        percentage: 85,
      },
    },
    {
      id: "3",
      title: "목표가 도달",
      message: "NAVER가 설정한 목표가 ₩185,000에 도달했습니다.",
      type: "info",
      category: "portfolio",
      isRead: true,
      createdAt: Date.now() - 3600000,
      metadata: {
        symbol: "035420",
        amount: 185000,
      },
    },
  ],
  settings: {
    trading: true,
    market: true,
    portfolio: true,
    ai: true,
    email: true,
    push: true,
    sms: false,
  },
  unreadCount: 2,
  isLoading: false,
  error: null,
}

export const fetchNotifications = createAsyncThunk("notification/fetchNotifications", async () => {
  // Simulate API call
  await new Promise((resolve) => setTimeout(resolve, 800))

  return initialState.notifications
})

export const markAsRead = createAsyncThunk("notification/markAsRead", async (notificationId: string) => {
  // Simulate API call
  await new Promise((resolve) => setTimeout(resolve, 300))

  return notificationId
})

export const markAllAsRead = createAsyncThunk("notification/markAllAsRead", async () => {
  // Simulate API call
  await new Promise((resolve) => setTimeout(resolve, 500))

  return true
})

export const updateSettings = createAsyncThunk(
  "notification/updateSettings",
  async (settings: Partial<NotificationSettings>) => {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 500))

    return settings
  },
)

export const notificationSlice = createSlice({
  name: "notification",
  initialState,
  reducers: {
    addNotification: (state, action: PayloadAction<Omit<Notification, "id" | "createdAt">>) => {
      const newNotification: Notification = {
        ...action.payload,
        id: Date.now().toString(),
        createdAt: Date.now(),
      }

      state.notifications.unshift(newNotification)
      if (!newNotification.isRead) {
        state.unreadCount += 1
      }
    },
    removeNotification: (state, action: PayloadAction<string>) => {
      const notification = state.notifications.find((n) => n.id === action.payload)
      if (notification && !notification.isRead) {
        state.unreadCount -= 1
      }
      state.notifications = state.notifications.filter((n) => n.id !== action.payload)
    },
    clearAllNotifications: (state) => {
      state.notifications = []
      state.unreadCount = 0
    },
    clearError: (state) => {
      state.error = null
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchNotifications.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(fetchNotifications.fulfilled, (state, action) => {
        state.isLoading = false
        state.notifications = action.payload
        state.unreadCount = action.payload.filter((n) => !n.isRead).length
      })
      .addCase(fetchNotifications.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || "알림을 가져오는데 실패했습니다"
      })
      .addCase(markAsRead.fulfilled, (state, action) => {
        const notification = state.notifications.find((n) => n.id === action.payload)
        if (notification && !notification.isRead) {
          notification.isRead = true
          state.unreadCount -= 1
        }
      })
      .addCase(markAllAsRead.fulfilled, (state) => {
        state.notifications.forEach((n) => {
          n.isRead = true
        })
        state.unreadCount = 0
      })
      .addCase(updateSettings.fulfilled, (state, action) => {
        state.settings = { ...state.settings, ...action.payload }
      })
  },
})

export const { addNotification, removeNotification, clearAllNotifications, clearError } = notificationSlice.actions
