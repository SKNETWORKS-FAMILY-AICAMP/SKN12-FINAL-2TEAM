import { createSlice, createAsyncThunk, type PayloadAction } from "@reduxjs/toolkit"

interface User {
  id: string
  email: string
  name: string
  avatar?: string
  role: string
  preferences: {
    theme: string
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
    // 로그인은 이미 app/auth/login/page.tsx에서 처리됨
    // 여기서는 더미 데이터 반환
    return {
      user: { id: "1", email, name: "User", role: "user", preferences: { theme: "dark", language: "ko", notifications: true } },
      token: "dummy-token"
    }
  },
)

export const logoutAsync = createAsyncThunk("auth/logout", async () => {
  // 로그아웃은 세션 클리어만 수행
  if (typeof window !== "undefined") {
    localStorage.removeItem("accessToken")
    localStorage.removeItem("refreshToken")
  }
})

export const refreshTokenAsync = createAsyncThunk("auth/refreshToken", async () => {
  // 토큰 갱신은 현재 구현되지 않음
  throw new Error("Token refresh not implemented")
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
  },
})

export const { clearError, updateUser } = authSlice.actions
