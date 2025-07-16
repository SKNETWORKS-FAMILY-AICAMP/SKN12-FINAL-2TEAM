interface LoginRequest {
  email: string
  password: string
}

interface RegisterRequest {
  email: string
  password: string
  name: string
}

interface AuthResponse {
  user: {
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
  token: string
  refreshToken: string
}

interface RefreshTokenResponse {
  token: string
  refreshToken: string
}

export const authApi = {
  async login(email: string, password: string): Promise<{ data: AuthResponse }> {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1000))

    // Mock successful login
    const mockResponse: AuthResponse = {
      user: {
        id: "1",
        email,
        name: "John Doe",
        avatar: "/avatars/user.jpg",
        role: "premium",
        preferences: {
          theme: "system",
          language: "ko",
          notifications: true,
        },
      },
      token: "mock-jwt-token-" + Date.now(),
      refreshToken: "mock-refresh-token-" + Date.now(),
    }

    // Simulate login validation
    if (email === "demo@example.com" && password === "demo123") {
      return { data: mockResponse }
    }

    throw new Error("Invalid credentials")
  },

  async register(data: RegisterRequest): Promise<{ data: AuthResponse }> {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 1200))

    const mockResponse: AuthResponse = {
      user: {
        id: Date.now().toString(),
        email: data.email,
        name: data.name,
        role: "basic",
        preferences: {
          theme: "system",
          language: "ko",
          notifications: true,
        },
      },
      token: "mock-jwt-token-" + Date.now(),
      refreshToken: "mock-refresh-token-" + Date.now(),
    }

    return { data: mockResponse }
  },

  async logout(): Promise<void> {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 500))

    // Clear local storage
    if (typeof window !== "undefined") {
      localStorage.removeItem("auth-token")
      localStorage.removeItem("refresh-token")
    }
  },

  async refreshToken(): Promise<{ data: RefreshTokenResponse }> {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 800))

    const mockResponse: RefreshTokenResponse = {
      token: "mock-jwt-token-refreshed-" + Date.now(),
      refreshToken: "mock-refresh-token-refreshed-" + Date.now(),
    }

    return { data: mockResponse }
  },

  async getProfile(): Promise<{ data: AuthResponse["user"] }> {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 600))

    const mockUser: AuthResponse["user"] = {
      id: "1",
      email: "demo@example.com",
      name: "John Doe",
      avatar: "/avatars/user.jpg",
      role: "premium",
      preferences: {
        theme: "system",
        language: "ko",
        notifications: true,
      },
    }

    return { data: mockUser }
  },

  async updateProfile(data: Partial<AuthResponse["user"]>): Promise<{ data: AuthResponse["user"] }> {
    // Simulate API call
    await new Promise((resolve) => setTimeout(resolve, 800))

    const currentUser = {
      id: "1",
      email: "demo@example.com",
      name: "John Doe",
      avatar: "/avatars/user.jpg",
      role: "premium",
      preferences: {
        theme: "system" as const,
        language: "ko",
        notifications: true,
      },
    }

    const updatedUser = { ...currentUser, ...data }
    return { data: updatedUser }
  },
}
