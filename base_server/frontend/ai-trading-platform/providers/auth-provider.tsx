"use client"

import type React from "react"
import { createContext, useContext, useEffect, useState } from "react"
import { authManager, type AuthUser, type AuthSession } from "@/lib/auth"

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
    // 실제 로그인은 로그인 페이지에서 처리하므로, 여기서는 세션 설정만 담당
    const session = authManager.getSession()
    if (session) {
      setUser(session.user)
    } else {
      // 이 경우는 직접 호출될 일이 거의 없지만, 방어 코드로 남겨둡니다.
      throw new Error("Login failed: No session found after login attempt.")
    }
  }

  const logout = async () => {
    authManager.clearSession()
    setUser(null)
    // 페이지를 새로고침하거나 로그인 페이지로 리다이렉트
    window.location.href = "/auth/login"
  }

  const updateUser = (userData: Partial<AuthUser>) => {
    const session = authManager.getSession()
    if (user && session) {
      const updatedUser = { ...user, ...userData }
      setUser(updatedUser)

      // Update session
      authManager.setSession({
        ...session,
        user: updatedUser,
      })
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