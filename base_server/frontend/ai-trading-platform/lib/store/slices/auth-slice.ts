import { createSlice, createAsyncThunk, type PayloadAction } from "@reduxjs/toolkit"
import { authApi } from "@/lib/api/auth"

interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: string
  preferences: {
    theme: "light" | "dark" | "system"
    language: string
    notifications: boolean
  }
}

interface AuthState {
  user: User | null
  token: string | null
  isLoading: boolean
  error: string | null
}

const initialState: AuthState = {
  user: null,
  token: null,
  isLoading: false,
  error: null,
}

export const loginAsync = createAsyncThunk(
  "auth/login",
  async ({ email, password }: { email: string; password: string }) => {
    const response = await authApi.login(email, password)
    return response.data
  },
)

export const logoutAsync = createAsyncThunk("auth/logout", async () => {
  await authApi.logout()
})

export const refreshTokenAsync = createAsyncThunk("auth/refreshToken", async () => {
  const response = await authApi.refreshToken()
  return response.data
})

export const authSlice = createSlice({
  name: "auth",
  initialState,
  reducers: {
    clearError: (state) => {
      state.error = null
    },
    updateUser: (state, action: PayloadAction<Partial<User>>) => {
      if (state.user) {
        state.user = { ...state.user, ...action.payload }
      }
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(loginAsync.pending, (state) => {
        state.isLoading = true
        state.error = null
      })
      .addCase(loginAsync.fulfilled, (state, action) => {
        state.isLoading = false
        state.user = action.payload.user
        state.token = action.payload.token
      })
      .addCase(loginAsync.rejected, (state, action) => {
        state.isLoading = false
        state.error = action.error.message || "로그인에 실패했습니다"
      })
      .addCase(logoutAsync.fulfilled, (state) => {
        state.user = null
        state.token = null
      })
      .addCase(refreshTokenAsync.fulfilled, (state, action) => {
        state.token = action.payload.token
      })
  },
})

export const { clearError, updateUser } = authSlice.actions
