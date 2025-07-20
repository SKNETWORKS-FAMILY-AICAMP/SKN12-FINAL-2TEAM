import { configureStore } from "@reduxjs/toolkit"
import { authSlice } from "./slices/auth-slice"
import { chatSlice } from "./slices/chat-slice"

export const store = configureStore({
  reducer: {
    auth: authSlice.reducer,
    chat: chatSlice.reducer,
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
