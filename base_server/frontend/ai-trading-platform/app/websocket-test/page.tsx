"use client"

import { useEffect, useState } from 'react'
import { useWebSocket } from '@/providers/websocket-provider'

export default function WebSocketTestPage() {
  const { isConnected, sendMessage, subscribe, unsubscribe } = useWebSocket()
  const [messages, setMessages] = useState<any[]>([])
  const [isSubscribed, setIsSubscribed] = useState(false)

  useEffect(() => {
    // 시장 데이터 구독
    subscribe('market_data', (data) => {
      setMessages(prev => [...prev, { ...data, timestamp: new Date().toISOString() }])
    })

    return () => {
      unsubscribe('market_data')
    }
  }, [subscribe, unsubscribe])

  const handleSubscribe = () => {
    if (!isSubscribed) {
      sendMessage({
        type: 'subscribe',
        symbols: ['005930', '051910'], // 삼성전자, LG화학
        indices: ['0001', '1001'] // KOSPI, KOSDAQ
      })
      setIsSubscribed(true)
    }
  }

  const handleUnsubscribe = () => {
    if (isSubscribed) {
      sendMessage({
        type: 'unsubscribe',
        symbols: ['005930', '051910'],
        indices: ['0001', '1001']
      })
      setIsSubscribed(false)
    }
  }

  const handlePing = () => {
    sendMessage({
      type: 'ping',
      timestamp: Date.now()
    })
  }

  const clearMessages = () => {
    setMessages([])
  }

  return (
    <div className="container mx-auto p-6">
      <h1 className="text-2xl font-bold mb-6">WebSocket 테스트</h1>
      
      {/* 연결 상태 */}
      <div className="mb-6 p-4 bg-gray-100 rounded">
        <h2 className="text-lg font-semibold mb-2">연결 상태</h2>
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full ${isConnected ? 'bg-green-500' : 'bg-red-500'}`}></div>
          <span>{isConnected ? '연결됨' : '연결 안됨'}</span>
        </div>
        <div className="mt-2">
          <span className="text-sm text-gray-600">
            구독 상태: {isSubscribed ? '구독 중' : '구독 안됨'}
          </span>
        </div>
      </div>

      {/* 컨트롤 버튼 */}
      <div className="mb-6 flex gap-4">
        <button
          onClick={handleSubscribe}
          disabled={!isConnected || isSubscribed}
          className="px-4 py-2 bg-blue-500 text-white rounded disabled:bg-gray-300"
        >
          구독 시작
        </button>
        <button
          onClick={handleUnsubscribe}
          disabled={!isConnected || !isSubscribed}
          className="px-4 py-2 bg-red-500 text-white rounded disabled:bg-gray-300"
        >
          구독 해제
        </button>
        <button
          onClick={handlePing}
          disabled={!isConnected}
          className="px-4 py-2 bg-green-500 text-white rounded disabled:bg-gray-300"
        >
          Ping
        </button>
        <button
          onClick={clearMessages}
          className="px-4 py-2 bg-gray-500 text-white rounded"
        >
          메시지 지우기
        </button>
      </div>

      {/* 메시지 로그 */}
      <div className="mb-6">
        <h2 className="text-lg font-semibold mb-2">메시지 로그 ({messages.length})</h2>
        <div className="bg-gray-100 p-4 rounded max-h-96 overflow-y-auto">
          {messages.length === 0 ? (
            <p className="text-gray-500">메시지가 없습니다.</p>
          ) : (
            <div className="space-y-2">
              {messages.map((msg, index) => (
                <div key={index} className="bg-white p-3 rounded border">
                  <div className="text-sm text-gray-500 mb-1">
                    {new Date(msg.timestamp).toLocaleTimeString()}
                  </div>
                  <pre className="text-xs overflow-x-auto">
                    {JSON.stringify(msg, null, 2)}
                  </pre>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>

      {/* 환경 정보 */}
      <div className="p-4 bg-gray-100 rounded">
        <h2 className="text-lg font-semibold mb-2">환경 정보</h2>
        <div className="text-sm space-y-1">
          <div>WebSocket URL: {process.env.NEXT_PUBLIC_WS_URL || 'ws://localhost:8000'}</div>
          <div>실제 WebSocket 사용: {process.env.NEXT_PUBLIC_USE_REAL_WEBSOCKET === 'true' ? '예' : '아니오'}</div>
        </div>
      </div>
    </div>
  )
} 