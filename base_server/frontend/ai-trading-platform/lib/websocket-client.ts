export class WebSocketClient {
  private ws: WebSocket | null = null;
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private isConnecting = false;
  private messageCallbacks: Map<string, (data: any) => void> = new Map();

  constructor(private url: string) {}

  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      if (this.isConnecting || this.ws?.readyState === WebSocket.OPEN) {
        console.log('이미 연결됨 또는 연결 중');
        resolve();
        return;
      }

      this.isConnecting = true;
      console.log('웹소켓 연결 시도:', this.url);
      
      try {
        this.ws = new WebSocket(this.url);
        
        this.ws.onopen = () => {
          console.log('웹소켓 연결 성공');
          this.isConnecting = false;
          this.reconnectAttempts = 0;
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            this.handleMessage(data);
          } catch (error) {
            console.error('웹소켓 메시지 파싱 에러:', error);
          }
        };

        this.ws.onclose = (event) => {
          console.log('웹소켓 연결 종료:', event.code, event.reason);
          this.isConnecting = false;
          
          if (!event.wasClean && this.reconnectAttempts < this.maxReconnectAttempts) {
            this.reconnect();
          }
        };

        this.ws.onerror = (error) => {
          console.error('웹소켓 에러:', error);
          this.isConnecting = false;
          reject(error);
        };

      } catch (error) {
        this.isConnecting = false;
        reject(error);
      }
    });
  }

  private reconnect() {
    this.reconnectAttempts++;
    console.log(`웹소켓 재연결 시도 ${this.reconnectAttempts}/${this.maxReconnectAttempts}`);
    
    setTimeout(() => {
      this.connect().catch(error => {
        console.error('웹소켓 재연결 실패:', error);
      });
    }, this.reconnectDelay * this.reconnectAttempts);
  }

  private handleMessage(data: any) {
    console.log('웹소켓 메시지 수신:', data);
    
    // 메시지 타입에 따른 콜백 호출
    if (data.type && this.messageCallbacks.has(data.type)) {
      const callback = this.messageCallbacks.get(data.type);
      if (callback) {
        callback(data);
      }
    }
  }

  onMessage(type: string, callback: (data: any) => void) {
    this.messageCallbacks.set(type, callback);
  }

  offMessage(type: string) {
    this.messageCallbacks.delete(type);
  }

  send(data: any) {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data));
    } else {
      console.error('웹소켓이 연결되지 않음');
    }
  }

  disconnect() {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.messageCallbacks.clear();
  }

  isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN;
  }
}

// 싱글톤 인스턴스
let websocketClient: WebSocketClient | null = null;

export function getWebSocketClient(): WebSocketClient {
  if (!websocketClient) {
    // 개발 환경에서는 localhost:8000 사용
    const apiBase = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';
    const wsUrl = apiBase.replace('http://', 'ws://').replace('https://', 'wss://');
    websocketClient = new WebSocketClient(`${wsUrl}/ws`);
    console.log('웹소켓 클라이언트 생성:', `${wsUrl}/ws`);
  }
  return websocketClient;
} 