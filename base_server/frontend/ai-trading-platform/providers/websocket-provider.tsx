"use client"

import type React from "react"
import { createContext, useContext, useEffect, useMemo, useRef, useState, useCallback } from "react"

interface WebSocketContextType {
  isConnected: boolean
  sendMessage: (message: any) => void
  subscribe: (channel: string, callback: (data: any) => void) => void
  unsubscribe: (channel: string) => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false)
  const wsRef = useRef<WebSocket | null>(null)
  const subscribersRef = useRef<Map<string, (data: any) => void>>(new Map())

  // Connect once on mount
  useEffect(() => {
    try {
      // In a real app, connect to your WebSocket server
      // wsRef.current = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws')
      setIsConnected(true)

      // Demo: simulate market data push
      const interval = setInterval(() => {
        const mockData = {
          type: "market_update",
          data: {
            symbol: "KOSPI",
            price: 2485 + Math.random() * 10 - 5,
            change: Math.random() * 2 - 1,
            timestamp: Date.now(),
          },
        }
        subscribersRef.current.forEach((callback, channel) => {
          if (channel === "market_data") {
            callback(mockData)
          }
        })
      }, 2000)

      return () => {
        clearInterval(interval)
        try { wsRef.current?.close() } catch {}
        wsRef.current = null
        setIsConnected(false)
      }
    } catch (error) {
      console.error("WebSocket connection failed:", error)
      setIsConnected(false)
    }
  }, [])

  const sendMessage = useCallback((message: any) => {
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }, [])

  const subscribe = useCallback((channel: string, callback: (data: any) => void) => {
    subscribersRef.current.set(channel, callback)
  }, [])

  const unsubscribe = useCallback((channel: string) => {
    subscribersRef.current.delete(channel)
  }, [])

  const value = useMemo(() => ({ isConnected, sendMessage, subscribe, unsubscribe }), [isConnected, sendMessage, subscribe, unsubscribe])

  return (
    <WebSocketContext.Provider value={value}>
      {children}
    </WebSocketContext.Provider>
  )
}

export function useWebSocket() {
  const context = useContext(WebSocketContext)
  if (context === undefined) {
    throw new Error("useWebSocket must be used within a WebSocketProvider")
  }
  return context
}
