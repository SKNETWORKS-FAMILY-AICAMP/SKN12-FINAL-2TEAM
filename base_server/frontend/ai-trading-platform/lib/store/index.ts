import { configureStore } from "@reduxjs/toolkit"
import { authSlice } from "./slices/auth-slice"
import { marketSlice } from "./slices/market-slice"
import { portfolioSlice } from "./slices/portfolio-slice"
import { chatSlice } from "./slices/chat-slice"
import { notificationSlice } from "./slices/notification-slice"

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    market: marketSlice.reducer,
    portfolio: portfolioSlice.reducer,
    chat: chatSlice.reducer,
    notification: notificationSlice.reducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ["persist/PERSIST"],
      },
    }),
})

export type RootState = ReturnType<typeof store.getState>
export type AppDispatch = typeof store.dispatch
