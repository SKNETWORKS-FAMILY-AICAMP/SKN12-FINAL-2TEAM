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
    setIsLoading(true)
    try {
      // 로그인은 이미 app/auth/login/page.tsx에서 처리되므로
      // 여기서는 세션만 확인하고 사용자 정보를 설정
      const session = authManager.getSession()
      if (session) {
        setUser(session.user)
        // 임시: 로그인 성공 시 무조건 온보딩 페이지로 이동
        if (typeof window !== "undefined") {
          window.location.href = "/onboarding"
        }
      } else {
        throw new Error("Login failed")
      }
    } catch (error) {
      throw new Error("Login failed")
    } finally {
      setIsLoading(false)
    }
  }

  const logout = async () => {
    try {
      // 로그아웃은 세션만 클리어하면 됨
      // API 호출은 필요하지 않음
    } catch (error) {
      console.error("Logout failed:", error)
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
