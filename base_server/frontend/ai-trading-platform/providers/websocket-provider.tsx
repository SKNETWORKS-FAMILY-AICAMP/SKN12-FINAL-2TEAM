"use client"

import type React from "react"
import { createContext, useContext, useEffect, useState } from "react"

interface WebSocketContextType {
  isConnected: boolean
  sendMessage: (message: any) => void
  subscribe: (channel: string, callback: (data: any) => void) => void
  unsubscribe: (channel: string) => void
}

const WebSocketContext = createContext<WebSocketContextType | undefined>(undefined)

export function WebSocketProvider({ children }: { children: React.ReactNode }) {
  const [isConnected, setIsConnected] = useState(false)
  const [ws, setWs] = useState<WebSocket | null>(null)
  const [subscribers, setSubscribers] = useState<Map<string, (data: any) => void>>(new Map())

  useEffect(() => {
    // Simulate WebSocket connection
    const connectWebSocket = () => {
      try {
        // In a real app, you would connect to your WebSocket server
        // const websocket = new WebSocket(process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000/ws')

        // For demo purposes, we'll simulate a connection
        setIsConnected(true)

        // Simulate receiving market data
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

          subscribers.forEach((callback, channel) => {
            if (channel === "market_data") {
              callback(mockData)
            }
          })
        }, 2000)

        return () => {
          clearInterval(interval)
          setIsConnected(false)
        }
      } catch (error) {
        console.error("WebSocket connection failed:", error)
        setIsConnected(false)
      }
    }

    const cleanup = connectWebSocket()
    return cleanup
  }, [subscribers])

  const sendMessage = (message: any) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }

  const subscribe = (channel: string, callback: (data: any) => void) => {
    setSubscribers((prev) => new Map(prev.set(channel, callback)))
  }

  const unsubscribe = (channel: string) => {
    setSubscribers((prev) => {
      const newMap = new Map(prev)
      newMap.delete(channel)
      return newMap
    })
  }

  return (
    <WebSocketContext.Provider value={{ isConnected, sendMessage, subscribe, unsubscribe }}>
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
