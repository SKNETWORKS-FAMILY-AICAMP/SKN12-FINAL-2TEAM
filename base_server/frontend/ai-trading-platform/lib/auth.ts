// Remove NextAuth dependency and use custom auth system
export interface AuthUser {
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

export interface AuthSession {
  user: AuthUser
  token: string
  refreshToken: string
  expiresAt: number
}

export class AuthManager {
  private static instance: AuthManager
  private session: AuthSession | null = null

  static getInstance(): AuthManager {
    if (!AuthManager.instance) {
      AuthManager.instance = new AuthManager()
    }
    return AuthManager.instance
  }

  setSession(session: AuthSession) {
    this.session = session
    if (typeof window !== "undefined") {
      localStorage.setItem("auth-session", JSON.stringify(session))
      // 다른 곳에서 토큰 직접 접근이 필요할 경우를 대비해 별도로 저장합니다.
      // AuthManager를 통해 접근하는 것이 가장 좋습니다.
      localStorage.setItem("accessToken", session.token)
      localStorage.setItem("refreshToken", session.refreshToken)
      if(session.user?.id) {
        localStorage.setItem("userId", session.user.id)
      }
    }
  }

  getSession(): AuthSession | null {
    if (this.session) {
      return this.session
    }

    if (typeof window !== "undefined") {
      const stored = localStorage.getItem("auth-session")
      if (stored) {
        try {
          const session = JSON.parse(stored) as AuthSession
          if (session.expiresAt > Date.now()) {
            this.session = session
            return session
          } else {
            this.clearSession()
          }
        } catch (error) {
          console.error("Failed to parse stored session:", error)
          this.clearSession()
        }
      }
    }

    return null
  }

  clearSession() {
    this.session = null
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth-session")
      localStorage.removeItem("accessToken")
      localStorage.removeItem("refreshToken")
    }
  }

  isAuthenticated(): boolean {
    const session = this.getSession()
    return session !== null && session.expiresAt > Date.now()
  }

  getUser(): AuthUser | null {
    const session = this.getSession()
    return session?.user || null
  }

  getToken(): string | null {
    const session = this.getSession()
    return session?.token || null
  }
}

export const authManager = AuthManager.getInstance() 