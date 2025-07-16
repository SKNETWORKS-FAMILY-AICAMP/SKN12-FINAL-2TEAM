import axios, { type AxiosInstance, type AxiosRequestConfig } from "axios"
import { store } from "@/lib/store"
import { refreshTokenAsync } from "@/lib/store/slices/auth-slice"

class ApiClient {
  private client: AxiosInstance
  private wsConnections: Map<string, WebSocket> = new Map()

  constructor() {
    this.client = axios.create({
      baseURL: process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000",
      timeout: 10000,
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
        const state = store.getState()
        const token = state.auth.token

        if (token) {
          config.headers.Authorization = `Bearer ${token}`
        }

        return config
      },
      (error) => Promise.reject(error),
    )

    // Response interceptor
    this.client.interceptors.response.use(
      (response) => response,
      async (error) => {
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
