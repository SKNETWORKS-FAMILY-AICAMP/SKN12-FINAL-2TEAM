"use client"

import { useState, useEffect } from 'react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { useAuth } from '@/hooks/use-auth'
import { useWebSocket } from '@/providers/websocket-provider'

interface RealtimeDataManagerProps {
  onDataUpdate?: (data: any) => void
}

export function RealtimeDataManager({ onDataUpdate }: RealtimeDataManagerProps) {
  const { token } = useAuth()
  const { isConnected, sendMessage } = useWebSocket()
  
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [isConnecting, setIsConnecting] = useState(false)
  const [subscribedSymbols, setSubscribedSymbols] = useState<string[]>([])
  const [subscribedIndices, setSubscribedIndices] = useState<string[]>([])
  const [newSymbols, setNewSymbols] = useState('')
  const [newIndices, setNewIndices] = useState('')
  const [status, setStatus] = useState<string>('')

  // 상태 조회
  const fetchStatus = async () => {
    if (!token) return
    
    try {
      const response = await fetch('/api/dashboard/realtime/status', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ accessToken: token })
      })
      
      if (response.ok) {
        const data = await response.json()
        setIsAuthenticated(data.is_authenticated)
        setSubscribedSymbols(data.subscribed_symbols || [])
        setSubscribedIndices(data.subscribed_indices || [])
        setStatus(data.is_connected ? '연결됨' : '연결 안됨')
      }
    } catch (error) {
      console.error('상태 조회 실패:', error)
    }
  }

  // OAuth 인증
  const handleAuthenticate = async () => {
    if (!token) return
    
    setIsConnecting(true)
    try {
      const response = await fetch('/api/dashboard/oauth/authenticate', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ accessToken: token })
      })
      
      if (response.ok) {
        const data = await response.json()
        setIsAuthenticated(true)
        setStatus('인증됨')
        console.log('OAuth 인증 성공:', data)
      } else {
        const error = await response.json()
        console.error('OAuth 인증 실패:', error)
        setStatus('인증 실패')
      }
    } catch (error) {
      console.error('OAuth 인증 에러:', error)
      setStatus('인증 에러')
    } finally {
      setIsConnecting(false)
    }
  }

  // 실시간 데이터 구독
  const handleSubscribe = async () => {
    if (!token || !isAuthenticated) return
    
    const symbols = newSymbols.split(',').map(s => s.trim()).filter(s => s)
    const indices = newIndices.split(',').map(i => i.trim()).filter(i => i)
    
    if (!symbols.length && !indices.length) return
    
    try {
      const response = await fetch('/api/dashboard/realtime/subscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          accessToken: token,
          symbols, 
          indices 
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setSubscribedSymbols(data.subscribed_symbols)
        setSubscribedIndices(data.subscribed_indices)
        setNewSymbols('')
        setNewIndices('')
        console.log('구독 성공:', data)
      } else {
        const error = await response.json()
        console.error('구독 실패:', error)
      }
    } catch (error) {
      console.error('구독 에러:', error)
    }
  }

  // 실시간 데이터 구독 해제
  const handleUnsubscribe = async (symbols: string[] = [], indices: string[] = []) => {
    if (!token || !isAuthenticated) return
    
    try {
      const response = await fetch('/api/dashboard/realtime/unsubscribe', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ 
          accessToken: token,
          symbols, 
          indices 
        })
      })
      
      if (response.ok) {
        const data = await response.json()
        setSubscribedSymbols(data.subscribed_symbols)
        setSubscribedIndices(data.subscribed_indices)
        console.log('구독 해제 성공:', data)
      } else {
        const error = await response.json()
        console.error('구독 해제 실패:', error)
      }
    } catch (error) {
      console.error('구독 해제 에러:', error)
    }
  }

  // 연결 해제
  const handleDisconnect = async () => {
    if (!token) return
    
    try {
      const response = await fetch('/api/dashboard/realtime/disconnect', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json'
        },
        body: JSON.stringify({ accessToken: token })
      })
      
      if (response.ok) {
        setIsAuthenticated(false)
        setSubscribedSymbols([])
        setSubscribedIndices([])
        setStatus('연결 해제됨')
        console.log('연결 해제 성공')
      }
    } catch (error) {
      console.error('연결 해제 에러:', error)
    }
  }

  // 예시 종목들
  const exampleSymbols = [
    { code: 'TSLA', name: 'Tesla' },
    { code: 'MSFT', name: 'Microsoft' },
    { code: 'AAPL', name: 'Apple' },
    { code: 'NKE', name: 'Nike' },
    { code: '005930', name: '삼성전자' },
    { code: '051910', name: 'LG화학' }
  ]

  const exampleIndices = [
    { code: '0001', name: 'KOSPI' },
    { code: '1001', name: 'KOSDAQ' }
  ]

  useEffect(() => {
    fetchStatus()
  }, [token])

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          실시간 데이터 관리
          <Badge variant={isAuthenticated ? "default" : "secondary"}>
            {status || (isAuthenticated ? '인증됨' : '미인증')}
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* OAuth 인증 */}
        <div className="space-y-2">
          <h3 className="text-sm font-medium">OAuth 인증</h3>
          <Button 
            onClick={handleAuthenticate} 
            disabled={isConnecting || isAuthenticated}
            className="w-full"
          >
            {isConnecting ? '인증 중...' : isAuthenticated ? '인증됨' : 'OAuth 인증'}
          </Button>
        </div>

        {/* 구독 추가 */}
        {isAuthenticated && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">새 종목 구독</h3>
            <div className="grid grid-cols-2 gap-2">
              <Input
                placeholder="종목 코드 (예: TSLA,MSFT)"
                value={newSymbols}
                onChange={(e) => setNewSymbols(e.target.value)}
              />
              <Input
                placeholder="지수 코드 (예: 0001,1001)"
                value={newIndices}
                onChange={(e) => setNewIndices(e.target.value)}
              />
            </div>
            <Button onClick={handleSubscribe} className="w-full">
              구독 추가
            </Button>
          </div>
        )}

        {/* 구독된 종목들 */}
        {subscribedSymbols.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">구독된 종목</h3>
            <div className="flex flex-wrap gap-1">
              {subscribedSymbols.map((symbol) => (
                <Badge key={symbol} variant="outline" className="cursor-pointer hover:bg-red-50"
                       onClick={() => handleUnsubscribe([symbol], [])}>
                  {symbol} ×
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* 구독된 지수들 */}
        {subscribedIndices.length > 0 && (
          <div className="space-y-2">
            <h3 className="text-sm font-medium">구독된 지수</h3>
            <div className="flex flex-wrap gap-1">
              {subscribedIndices.map((index) => (
                <Badge key={index} variant="outline" className="cursor-pointer hover:bg-red-50"
                       onClick={() => handleUnsubscribe([], [index])}>
                  {index} ×
                </Badge>
              ))}
            </div>
          </div>
        )}

        {/* 예시 종목들 */}
        <div className="space-y-2">
          <h3 className="text-sm font-medium">예시 종목</h3>
          <div className="grid grid-cols-2 gap-2">
            <div>
              <p className="text-xs text-gray-500 mb-1">주요 종목</p>
              <div className="space-y-1">
                {exampleSymbols.map((item) => (
                  <Button
                    key={item.code}
                    variant="outline"
                    size="sm"
                    className="w-full justify-between text-xs"
                    onClick={() => setNewSymbols(prev => prev ? `${prev},${item.code}` : item.code)}
                  >
                    <span>{item.name}</span>
                    <span className="text-gray-500">{item.code}</span>
                  </Button>
                ))}
              </div>
            </div>
            <div>
              <p className="text-xs text-gray-500 mb-1">지수</p>
              <div className="space-y-1">
                {exampleIndices.map((item) => (
                  <Button
                    key={item.code}
                    variant="outline"
                    size="sm"
                    className="w-full justify-between text-xs"
                    onClick={() => setNewIndices(prev => prev ? `${prev},${item.code}` : item.code)}
                  >
                    <span>{item.name}</span>
                    <span className="text-gray-500">{item.code}</span>
                  </Button>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* 연결 해제 */}
        {isAuthenticated && (
          <Button 
            onClick={handleDisconnect} 
            variant="destructive" 
            className="w-full"
          >
            연결 해제
          </Button>
        )}
      </CardContent>
    </Card>
  )
} 