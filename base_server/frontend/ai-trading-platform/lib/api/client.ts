import axios, { type AxiosInstance, type AxiosRequestConfig } from "axios"
import { store } from "@/lib/store"
import { refreshTokenAsync } from "@/lib/store/slices/auth-slice"

class ApiClient {
  private client: AxiosInstance
  private wsConnections: Map<string, WebSocket> = new Map()

  constructor() {
    const baseURL = process.env.NEXT_PUBLIC_API_URL;
    if (!baseURL) {
      throw new Error("NEXT_PUBLIC_API_URL 환경변수가 설정되어 있지 않습니다. .env.local 파일에 NEXT_PUBLIC_API_URL을 지정하세요.");
    }
    // Normalize baseURL: if pointing to backend root without /api, append /api
    let normalizedBaseURL = baseURL.trim()
    if (normalizedBaseURL.endsWith('/')) {
      normalizedBaseURL = normalizedBaseURL.slice(0, -1)
    }
    const isHttp = /^https?:\/\//.test(normalizedBaseURL)
    if (isHttp && !normalizedBaseURL.endsWith('/api')) {
      normalizedBaseURL = `${normalizedBaseURL}/api`
    }
    const timeout = process.env.NEXT_PUBLIC_API_TIMEOUT
      ? parseInt(process.env.NEXT_PUBLIC_API_TIMEOUT, 10)
      : 10000;
    this.client = axios.create({
      baseURL: normalizedBaseURL,
      timeout,
      headers: {
        "Content-Type": "application/json",
      },
    })
    this.setupInterceptors()
  }

  private setupInterceptors() {
    // Request interceptor
    this.client.interceptors.request.use(
      (config) => {
        // accessToken을 localStorage에서 읽음 (클라이언트 환경에서만)
        let token = "";
        if (typeof window !== "undefined") {
          token = localStorage.getItem("accessToken") || "";
        }

        if (token) {
          config.headers.Authorization = `Bearer ${token}`;
        }

        // accessToken, sequence 자동 주입 (BaseRequest 호환)
        if (
          config.method &&
          ["post", "put"].includes(config.method.toLowerCase()) &&
          typeof config.data === "object" &&
          config.data !== null
        ) {
          config.data = {
            ...config.data,
            accessToken: token,
            sequence: Date.now(),
          };
        }

        return config;
      },
      (error) => Promise.reject(error),
    );

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => {
        try {
          if (typeof response.data === "string") {
            const trimmed = response.data.trim()
            if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
              response.data = JSON.parse(trimmed)
            }
          }
        } catch (_e) {
          // ignore parse errors; leave as string
        }
        return response
      },
      async (error) => {
        if (error.code === 'ECONNABORTED') {
          // 이미 로그인된 상태라면
          if (typeof window !== 'undefined') {
            const authManager = require("@/lib/auth").authManager;
            if (authManager.isLoggedIn && authManager.isLoggedIn()) {
              window.alert("장시간 사용이 없어 로그아웃 되었습니다.");
              authManager.clearSession();
              window.location.href = "/auth/login";
              return;
            }
          }
        }
        const originalRequest = error.config

        if (error.response?.status === 401 && !originalRequest._retry) {
          originalRequest._retry = true

          try {
            await store.dispatch(refreshTokenAsync())
            return this.client(originalRequest)
          } catch (refreshError) {
            // Redirect to login
            window.location.href = "/auth/login"
            return Promise.reject(refreshError)
          }
        }

        return Promise.reject(error)
      },
    )
  }

  // HTTP Methods
  async get<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.get(url, config)
    return response.data
  }

  async post<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.post(url, data, config)
    return response.data
  }

  async put<T>(url: string, data?: any, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.put(url, data, config)
    return response.data
  }

  async delete<T>(url: string, config?: AxiosRequestConfig): Promise<T> {
    const response = await this.client.delete(url, config)
    return response.data
  }

  // WebSocket Methods
  connectWebSocket(endpoint: string, onMessage?: (data: any) => void): WebSocket {
    const wsUrl = `${process.env.NEXT_PUBLIC_WS_URL || "ws://localhost:8000"}${endpoint}`
    const ws = new WebSocket(wsUrl)

    ws.onopen = () => {
      console.log(`WebSocket connected: ${endpoint}`)
    }

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      onMessage?.(data)
    }

    ws.onclose = () => {
      console.log(`WebSocket disconnected: ${endpoint}`)
      this.wsConnections.delete(endpoint)
    }

    ws.onerror = (error) => {
      console.error(`WebSocket error: ${endpoint}`, error)
    }

    this.wsConnections.set(endpoint, ws)
    return ws
  }

  disconnectWebSocket(endpoint: string) {
    const ws = this.wsConnections.get(endpoint)
    if (ws) {
      ws.close()
      this.wsConnections.delete(endpoint)
    }
  }

  sendWebSocketMessage(endpoint: string, message: any) {
    const ws = this.wsConnections.get(endpoint)
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }
}

export const apiClient = new ApiClient()
