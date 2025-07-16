export const API_ENDPOINTS = {
  // Authentication
  AUTH: {
    LOGIN: "/auth/login",
    LOGOUT: "/auth/logout",
    REGISTER: "/auth/register",
    REFRESH: "/auth/refresh",
    PROFILE: "/auth/profile",
  },

  // Dashboard
  DASHBOARD: {
    OVERVIEW: "/dashboard/overview",
    MARKET_DATA: "/dashboard/market",
    PORTFOLIO_SUMMARY: "/dashboard/portfolio",
    AI_INSIGHTS: "/dashboard/ai-insights",
  },

  // Chat
  CHAT: {
    CONVERSATIONS: "/chat/conversations",
    MESSAGES: "/chat/messages",
    SEND_MESSAGE: "/chat/send",
    AI_TOOLS: "/chat/tools",
  },

  // Portfolio
  PORTFOLIO: {
    LIST: "/portfolio",
    DETAILS: "/portfolio/:id",
    TRANSACTIONS: "/portfolio/transactions",
    PERFORMANCE: "/portfolio/performance",
  },

  // Market
  MARKET: {
    OVERVIEW: "/market/overview",
    STOCKS: "/market/stocks",
    INDICES: "/market/indices",
    NEWS: "/market/news",
    ANALYSIS: "/market/analysis",
  },

  // Auto Trading
  AUTOTRADE: {
    STRATEGIES: "/autotrade/strategies",
    SIGNALS: "/autotrade/signals",
    BACKTEST: "/autotrade/backtest",
    EXECUTE: "/autotrade/execute",
  },

  // Notifications
  NOTIFICATIONS: {
    LIST: "/notifications",
    MARK_READ: "/notifications/:id/read",
    SETTINGS: "/notifications/settings",
  },

  // Settings
  SETTINGS: {
    PROFILE: "/settings/profile",
    PREFERENCES: "/settings/preferences",
    SECURITY: "/settings/security",
    API_KEYS: "/settings/api-keys",
  },
}

// WebSocket endpoints
export const WS_ENDPOINTS = {
  MARKET_DATA: "/ws/market",
  CHAT: "/ws/chat",
  NOTIFICATIONS: "/ws/notifications",
  PORTFOLIO: "/ws/portfolio",
  TRADING_SIGNALS: "/ws/trading-signals",
}
