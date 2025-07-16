"use client"

import type React from "react"
import { createContext, useContext, useEffect, useState } from "react"
import { authManager, type AuthUser, type AuthSession } from "@/lib/auth"
import { authApi } from "@/lib/api/auth"

interface AuthContextType {
  user: AuthUser | null
  isLoading: boolean
  login: (email: string, password: string) => Promise<void>
  logout: () => Promise<void>
  updateUser: (userData: Partial<AuthUser>) => void
}

const AuthContext = createContext<AuthContextType | undefined>(undefined)

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Check for existing session on mount
    const checkAuth = async () => {
      try {
        const existingSession = authManager.getSession()
        if (existingSession) {
          setUser(existingSession.user)
        }
      } catch (error) {
        console.error("Auth check failed:", error)
        authManager.clearSession()
      } finally {
        setIsLoading(false)
      }
    }

    checkAuth()
  }, [])

  const login = async (email: string, password: string) => {
    setIsLoading(true)
    try {
      const response = await authApi.login(email, password)
      const { user: userData, token } = response.data

      const session: AuthSession = {
        user: userData,
        token,
        expiresAt: Date.now() + 24 * 60 * 60 * 1000, // 24 hours
      }

      authManager.setSession(session)
      setUser(userData)

      // 임시: 로그인 성공 시 무조건 온보딩 페이지로 이동
      if (typeof window !== "undefined") {
        window.location.href = "/onboarding"
      }
      // TODO: 나중에 userData.login_count === 0 일 때만 /onboarding, 아니면 /dashboard로 분기
    } catch (error) {
      throw new Error("Login failed")
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      await authApi.logout()
    } catch (error) {
      console.error("Logout API call failed:", error)
    } finally {
      authManager.clearSession()
      setUser(null)
    }
  }

  const updateUser = (userData: Partial<AuthUser>) => {
    if (user) {
      const updatedUser = { ...user, ...userData }
      setUser(updatedUser)

      // Update session
      const session = authManager.getSession()
      if (session) {
        authManager.setSession({
          ...session,
          user: updatedUser,
        })
      }
    }
  }

  return <AuthContext.Provider value={{ user, isLoading, login, logout, updateUser }}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider")
  }
  return context
}
