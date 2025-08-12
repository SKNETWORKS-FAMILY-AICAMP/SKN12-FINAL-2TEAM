// 한국투자증권 OpenAPI 클라이언트
// tests.py의 로직을 TypeScript로 변환

export interface TokenData {
  access_token: string;
  expires_at: number;
}

export interface DomesticPrice {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume?: number;
  high?: number;
  low?: number;
  open?: number;
  prev_close?: number;
  timestamp: string;
}

export interface OverseasDetail {
  symbol: string;
  market: string;
  last: number;
  change: number;
  change_pct: number;
  open: number;
  high: number;
  low: number;
  volume: number;
  currency: string;
  timestamp: string;
}

export interface IndexData {
  name: string;
  code: string;
  value: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

export interface StockData {
  symbol: string;
  price: number;
  change: number;
  change_pct: number;
  volume: number;
  timestamp: string;
}

class TokenManager {
  private appkey: string;
  private appsecret: string;
  private mode: string;
  private token: string | null = null;
  private expiresAt: number = 0;
  private tokenPromise: Promise<string> | null = null; // 중복 요청 방지용

  constructor(appkey: string, appsecret: string, mode: string = "prod") {
    this.appkey = appkey;
    this.appsecret = appsecret;
    this.mode = mode;
  }

  private async requestNewToken(): Promise<string> {
    const base = this.mode === "prod" 
      ? "https://openapi.koreainvestment.com:9443"
      : "https://openapivts.koreainvestment.com:29443";
    
    const url = `${base}/oauth2/tokenP`;
    const body = {
      grant_type: "client_credentials",
      appkey: this.appkey,
      appsecret: this.appsecret,
    };

    try {
      console.log('Requesting new token from Korea Investment API via proxy...');
      
      // 백엔드 프록시를 통해 한국투자증권 API 호출
      const response = await fetch('/api/proxy/korea-invest/token', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json; charset=UTF-8',
        },
        body: JSON.stringify({
          url: url,
          body: body,
          mode: this.mode
        }),
      });

      if (!response.ok) {
        const errorText = await response.text();
        console.error(`Token request failed: ${response.status} - ${errorText}`);
        
        // 백엔드 서버가 실행되지 않았거나 API 키 문제가 있을 때 Mock 토큰 반환
        if (response.status === 500 || response.status === 502) {
          console.warn('백엔드 서버 연결 실패. Mock 토큰을 사용합니다.');
          return 'mock_token_for_development';
        }
        
        throw new Error(`Token request failed: ${response.status}`);
      }

      const data = await response.json();
      this.token = data.access_token;
      this.expiresAt = Date.now() + (data.expires_in * 1000) - 60000; // 1분 여유
      
      console.log('Token obtained successfully');
      
      return this.token!;
    } catch (error) {
      console.error('Token request error:', error);
      
      // 네트워크 오류나 기타 문제로 토큰을 가져올 수 없을 때 Mock 토큰 반환
      console.warn('토큰 요청 실패. Mock 토큰을 사용합니다.');
      return 'mock_token_for_development';
    }
  }

  async getToken(): Promise<string> {
    // 토큰이 유효하면 반환
    if (this.token && Date.now() < this.expiresAt) {
      return this.token;
    }

    // 이미 토큰 요청 중이면 기존 Promise 반환
    if (this.tokenPromise) {
      return this.tokenPromise;
    }

    // 새로운 토큰 요청 시작
    this.tokenPromise = this.requestNewTokenWithRetry();
    
    try {
      const token = await this.tokenPromise;
      return token;
    } finally {
      this.tokenPromise = null; // 요청 완료 후 초기화
    }
  }

  private async requestNewTokenWithRetry(maxRetries: number = 3): Promise<string> {
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        return await this.requestNewToken();
      } catch (error) {
        console.error(`Token request attempt ${attempt} failed:`, error);
        
        if (attempt === maxRetries) {
          throw error; // 마지막 시도에서 실패하면 에러 throw
        }
        
        // 재시도 전 대기 (지수 백오프)
        const delay = Math.pow(2, attempt) * 1000; // 2초, 4초, 8초
        console.log(`Retrying token request in ${delay}ms...`);
        await new Promise(resolve => setTimeout(resolve, delay));
      }
    }
    
    throw new Error('Token request failed after all retries');
  }
}

export class KoreaInvestClient {
  private tokenManager: TokenManager;
  private appkey: string;
  private appsecret: string;
  private mode: string;
  private baseUrl: string;

  static readonly DOMESTIC_TRID = "FHKST01010100";
  static readonly OVERSEAS_TRID = "HHDFS76200200";

  constructor(appkey: string, appsecret: string, mode: string = "prod") {
    this.tokenManager = new TokenManager(appkey, appsecret, mode);
    this.appkey = appkey;
    this.appsecret = appsecret;
    this.mode = mode;
    this.baseUrl = mode === "prod"
      ? "https://openapi.koreainvestment.com:9443"
      : "https://openapivts.koreainvestment.com:29443";
  }

  private async getHeaders(trId: string): Promise<Record<string, string>> {
    const token = await this.tokenManager.getToken();
    return {
      "content-type": "application/json; charset=utf-8",
      "authorization": `Bearer ${token}`,
      "appkey": this.appkey,
      "appsecret": this.appsecret,
      "tr_id": trId,
      "custtype": "P", // 개인
    };
  }

  // 국내 주식 현재가 조회
  async getDomesticPrice(symbol: string): Promise<DomesticPrice> {
    const url = `${this.baseUrl}/uapi/domestic-stock/v1/quotations/inquire-price`;
    const params = new URLSearchParams({
      "FID_COND_MRKT_DIV_CODE": "J",
      "FID_INPUT_ISCD": symbol,
    });

    const headers = await this.getHeaders(KoreaInvestClient.DOMESTIC_TRID);
    
    // 시장 개장 상태 확인
    const isMarketOpen = isKoreaMarketOpen();
    console.log(`한국 시장 상태: ${isMarketOpen ? '개장' : '마감'}`);
    
    // 시장 상태에 따른 재시도 횟수 결정
    const maxRetries = isMarketOpen ? 5 : 1; // 장이 닫혀있으면 1번만 시도
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`국내 주식 데이터 조회 시작: ${symbol} (시도 ${attempt}/${maxRetries})`);
        console.log(`요청 URL: ${url}?${params}`);
        console.log(`요청 헤더:`, headers);
        
        // 백엔드 프록시를 통해 한국투자증권 API 호출
        const response = await fetch('/api/proxy/korea-invest/domestic-price', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json; charset=UTF-8',
          },
          body: JSON.stringify({
            url: `${url}?${params}`,
            headers: headers,
            mode: this.mode
          }),
        });

        console.log(`API 응답 상태: ${response.status}`);

        if (!response.ok) {
          const errorText = await response.text();
          console.error(`API 에러 응답: ${response.status} - ${errorText}`);
          
          // 백엔드 서버가 실행되지 않았거나 API 키 문제가 있을 때 Mock 데이터 반환
          if (response.status === 500 || response.status === 502) {
            console.warn('백엔드 서버 연결 실패. Mock 데이터를 사용합니다.');
            return this.getMockDomesticPrice(symbol);
          }
          
          throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        console.log(`한국투자증권 API 응답:`, data);
        
        const output = data.output || {};
        const price = this.toFloat(output.stck_prpr);
        
        // 가격이 0이거나 유효하지 않은 경우 재시도
        if (price <= 0) {
          console.warn(`${symbol} 가격이 유효하지 않음 (${price}), 재시도 중...`);
          if (attempt < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1초 대기
            continue;
          }
        }

        return {
          symbol,
          price: price,
          change: this.toFloat(output.prdy_vrss),
          change_pct: this.toFloat(output.prdy_ctrt),
          volume: this.toInt(output.acml_vol),
          high: this.toFloat(output.stck_hgpr),
          low: this.toFloat(output.stck_lwpr),
          open: this.toFloat(output.stck_oprc),
          prev_close: this.toFloat(output.prdy_clpr),
          timestamp: new Date().toISOString(),
        };
      } catch (error) {
        console.error(`국내 주식 데이터 조회 오류 (${symbol}, 시도 ${attempt}/${maxRetries}):`, error);
        
        if (attempt === maxRetries) {
          // 마지막 시도에서 실패하면 Mock 데이터 반환
          console.warn('모든 시도 실패. Mock 데이터를 사용합니다.');
          return this.getMockDomesticPrice(symbol);
        }
        
        // 재시도 전 1초 대기
        console.log(`${symbol} 재시도 대기 중... (${attempt}/${maxRetries})`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    // 모든 시도 실패 시 Mock 데이터 반환
    return this.getMockDomesticPrice(symbol);
  }

  // Mock 국내 주식 데이터 생성
  private getMockDomesticPrice(symbol: string): DomesticPrice {
    const basePrice = symbol === '005930' ? 75000 : symbol === '000660' ? 150000 : 50000;
    const change = Math.random() * 2000 - 1000; // -1000 ~ +1000
    const price = basePrice + change;
    const changePct = (change / basePrice) * 100;
    
    return {
      symbol,
      price: Math.round(price),
      change: Math.round(change),
      change_pct: Math.round(changePct * 100) / 100,
      volume: Math.floor(Math.random() * 1000000) + 100000,
      high: Math.round(price * 1.02),
      low: Math.round(price * 0.98),
      open: Math.round(price * 1.01),
      prev_close: basePrice,
      timestamp: new Date().toISOString(),
    };
  }

  // 해외 주식 상세 조회
  async getOverseasDetail(excd: string, symb: string): Promise<OverseasDetail> {
    const url = `${this.baseUrl}/uapi/overseas-price/v1/quotations/price-detail`;
    const params = new URLSearchParams({
      "AUTH": " ",
      "EXCD": excd,
      "SYMB": symb,
    });

    const headers = await this.getHeaders(KoreaInvestClient.OVERSEAS_TRID);
    
    // 5번 재시도 로직
    for (let attempt = 1; attempt <= 5; attempt++) {
      try {
        console.log(`해외 주식 데이터 조회 시작: ${symb} (${excd}) (시도 ${attempt}/5)`);
        
        const response = await fetch('/api/proxy/korea-invest/overseas-detail', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json; charset=UTF-8',
          },
          body: JSON.stringify({
            url: `${url}?${params}`,
            headers: headers,
            mode: this.mode
          }),
        });

        if (!response.ok) {
          throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        const output = data.output || {};

        const last = this.toFloat(output.last);
        
        // 가격이 0이거나 유효하지 않은 경우 재시도
        if (last <= 0) {
          console.warn(`${symb} 해외 주식 가격이 유효하지 않음 (${last}), 재시도 중...`);
          if (attempt < 5) {
            await new Promise(resolve => setTimeout(resolve, 1000)); // 1초 대기
            continue;
          }
        }

        const base = this.toFloat(output.base);
        const change = last - base;
        const changePct = base !== 0 ? (change / base) * 100 : 0;

        return {
          symbol: symb,
          market: excd,
          last,
          change,
          change_pct: changePct,
          open: this.toFloat(output.open),
          high: this.toFloat(output.high),
          low: this.toFloat(output.low),
          volume: this.toInt(output.tvol),
          currency: output.curr || "",
          timestamp: new Date().toISOString(),
        };
      } catch (error) {
        console.error(`해외 주식 데이터 조회 오류 (${symb}, 시도 ${attempt}/5):`, error);
        
        if (attempt === 5) {
          // 마지막 시도에서 실패하면 에러 throw
          throw error;
        }
        
        // 재시도 전 1초 대기
        console.log(`${symb} 재시도 대기 중... (${attempt}/5)`);
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    throw new Error(`해외 주식 데이터 조회 실패: ${symb} - 5번 시도 후에도 성공하지 못함`);
  }

  // 지수 데이터 조회 (WebSocket/REST 전환 전략)
  async getIndexData(indexCode: string, region: 'KR' | 'US' = 'KR'): Promise<IndexData> {
    const dataSource = getMarketDataSource(region);
    console.log(`${indexCode} 지수 데이터 조회 (${region} 시장, ${dataSource} 소스)`);

    if (dataSource === 'websocket') {
      // WebSocket을 통한 실시간 데이터는 별도 WebSocket 클라이언트에서 처리
      // 여기서는 WebSocket 연결 상태를 확인하고 대기
      console.log(`${indexCode} WebSocket 실시간 데이터 대기 중...`);
      throw new Error(`${indexCode} WebSocket 실시간 데이터는 별도 처리됩니다.`);
    }

    // REST API를 통한 마감/지연 데이터 조회
    return this.getIndexDataViaRest(indexCode, region);
  }

  // REST API를 통한 지수 데이터 조회
  private async getIndexDataViaRest(indexCode: string, region: 'KR' | 'US'): Promise<IndexData> {
    const config = REST_API_CONFIG[region];
    
    if (region === 'KR') {
      return this.getKoreaIndexDataViaRest(indexCode, config.indices);
    } else {
      return this.getUSIndexDataViaRest(indexCode, config.indices);
    }
  }

  // 한국 지수 REST API 조회
  private async getKoreaIndexDataViaRest(indexCode: string, config: any): Promise<IndexData> {
    const indexMap: Record<string, { name: string; symbol: string }> = {
      'KOSPI': { name: 'KOSPI', symbol: '0001' },
      'KOSDAQ': { name: 'KOSDAQ', symbol: '1001' },
      'KOSPI200': { name: 'KOSPI200', symbol: '1002' }
    };

    const indexInfo = indexMap[indexCode];
    if (!indexInfo) {
      throw new Error(`지원하지 않는 한국 지수: ${indexCode}`);
    }

    // 시장 개장 상태 확인
    const isMarketOpen = isKoreaMarketOpen();
    console.log(`한국 시장 상태: ${isMarketOpen ? '개장' : '마감'}`);

    // 지수 조회 전용 엔드포인트와 TR-ID 사용
    const url = `${this.baseUrl}/uapi/domestic-stock/v1/quotations/inquire-index`;
    const params = new URLSearchParams({
      "FID_COND_MRKT_DIV_CODE": "J",
      "FID_INPUT_ISCD": indexInfo.symbol,
    });

    // 지수 조회 전용 TR-ID 사용
    const headers = await this.getHeaders("FHKIM04010100");
    
    // 시장 상태에 따른 재시도 횟수 결정
    const maxRetries = isMarketOpen ? 5 : 1; // 장이 닫혀있으면 1번만 시도
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`한국 지수 REST API 조회: ${indexCode} (${indexInfo.symbol}) (시도 ${attempt}/${maxRetries})`);
        console.log(`요청 URL: ${url}?${params}`);
        console.log(`요청 헤더:`, headers);
        
        const response = await fetch('/api/proxy/korea-invest/korea-index', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json; charset=UTF-8',
          },
          body: JSON.stringify({
            url: `${url}?${params}`,
            headers: headers,
            mode: this.mode
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error(`API 에러 응답: ${response.status} - ${errorText}`);
          
          // 백엔드 서버가 실행되지 않았거나 API 키 문제가 있을 때 Mock 데이터 반환
          if (response.status === 500 || response.status === 502) {
            console.warn('백엔드 서버 연결 실패. Mock 데이터를 사용합니다.');
            return this.getMockKoreaIndexData(indexCode);
          }
          
          throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        console.log(`한국투자증권 지수 API 응답:`, data);
        
        const output = data.output || {};
        const value = this.toFloat(output.stck_prpr);
        
        if (value <= 0) {
          console.warn(`${indexCode} 지수 값이 유효하지 않음 (${value}), 재시도 중...`);
          if (attempt < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            continue;
          }
        }

        return {
          name: indexInfo.name,
          code: indexCode,
          value: value,
          change: this.toFloat(output.prdy_vrss),
          change_pct: this.toFloat(output.prdy_ctrt),
          volume: this.toInt(output.acml_vol),
          timestamp: new Date().toISOString(),
        };
      } catch (error) {
        console.error(`한국 지수 REST API 오류 (${indexCode}, 시도 ${attempt}/${maxRetries}):`, error);
        
        if (attempt === maxRetries) {
          // 마지막 시도에서 실패하면 Mock 데이터 반환
          console.warn('모든 시도 실패. Mock 데이터를 사용합니다.');
          return this.getMockKoreaIndexData(indexCode);
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    // 모든 시도 실패 시 Mock 데이터 반환
    return this.getMockKoreaIndexData(indexCode);
  }

  // Mock 한국 지수 데이터 생성
  private getMockKoreaIndexData(indexCode: string): IndexData {
    const baseValues: Record<string, { name: string; value: number }> = {
      'KOSPI': { name: 'KOSPI', value: 2500 },
      'KOSDAQ': { name: 'KOSDAQ', value: 850 },
      'KOSPI200': { name: 'KOSPI200', value: 330 }
    };

    const baseData = baseValues[indexCode];
    if (!baseData) {
      throw new Error(`지원하지 않는 한국 지수: ${indexCode}`);
    }

    const change = Math.random() * 20 - 10; // -10 ~ +10
    const value = baseData.value + change;
    const changePct = (change / baseData.value) * 100;
    
    return {
      name: baseData.name,
      code: indexCode,
      value: Math.round(value * 100) / 100,
      change: Math.round(change * 100) / 100,
      change_pct: Math.round(changePct * 100) / 100,
      volume: Math.floor(Math.random() * 1000000000) + 100000000,
      timestamp: new Date().toISOString(),
    };
  }

  // 미국 지수 REST API 조회
  private async getUSIndexDataViaRest(indexCode: string, config: any): Promise<IndexData> {
    const indexMap: Record<string, { name: string; excd: string; symb: string }> = {
      'S&P500': { name: 'S&P 500', excd: 'NYS', symb: 'INX' },
      'DOW': { name: 'Dow Jones', excd: 'NYS', symb: 'DJI' },
      'NASDAQ': { name: 'NASDAQ', excd: 'NAS', symb: 'IXIC' }
    };

    const indexInfo = indexMap[indexCode];
    if (!indexInfo) {
      throw new Error(`지원하지 않는 미국 지수: ${indexCode}`);
    }

    // 시장 개장 상태 확인
    const isMarketOpen = isUSMarketOpen();
    console.log(`미국 시장 상태: ${isMarketOpen ? '개장' : '마감'}`);

    const url = `${this.baseUrl}${config.endpoint}`;
    const params = new URLSearchParams({
      "AUTH": "N",
      "EXCD": indexInfo.excd,
      "SYMB": indexInfo.symb,
    });

    const headers = await this.getHeaders(config.tr_id);
    
    // 시장 상태에 따른 재시도 횟수 결정
    const maxRetries = isMarketOpen ? 5 : 1; // 장이 닫혀있으면 1번만 시도
    
    for (let attempt = 1; attempt <= maxRetries; attempt++) {
      try {
        console.log(`미국 지수 REST API 조회: ${indexCode} (${indexInfo.excd}:${indexInfo.symb}) (시도 ${attempt}/${maxRetries})`);
        
        const response = await fetch('/api/proxy/korea-invest/us-index', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json; charset=UTF-8',
          },
          body: JSON.stringify({
            url: `${url}?${params}`,
            headers: headers,
            mode: this.mode
          }),
        });

        if (!response.ok) {
          const errorText = await response.text();
          console.error(`API 에러 응답: ${response.status} - ${errorText}`);
          
          // 백엔드 서버가 실행되지 않았거나 API 키 문제가 있을 때 Mock 데이터 반환
          if (response.status === 500 || response.status === 502) {
            console.warn('백엔드 서버 연결 실패. Mock 데이터를 사용합니다.');
            return this.getMockUSIndexData(indexCode);
          }
          
          throw new Error(`API request failed: ${response.status}`);
        }

        const data = await response.json();
        const output = data.output || {};
        const value = this.toFloat(output.last);
        
        if (value <= 0) {
          console.warn(`${indexCode} 지수 값이 유효하지 않음 (${value}), 재시도 중...`);
          if (attempt < maxRetries) {
            await new Promise(resolve => setTimeout(resolve, 1000));
            continue;
          }
        }

        const base = this.toFloat(output.base);
        const change = value - base;
        const changePct = base !== 0 ? (change / base) * 100 : 0;

        return {
          name: indexInfo.name,
          code: indexCode,
          value: value,
          change: change,
          change_pct: changePct,
          volume: this.toInt(output.tvol),
          timestamp: new Date().toISOString(),
        };
      } catch (error) {
        console.error(`미국 지수 REST API 오류 (${indexCode}, 시도 ${attempt}/${maxRetries}):`, error);
        
        if (attempt === maxRetries) {
          // 마지막 시도에서 실패하면 Mock 데이터 반환
          console.warn('모든 시도 실패. Mock 데이터를 사용합니다.');
          return this.getMockUSIndexData(indexCode);
        }
        
        await new Promise(resolve => setTimeout(resolve, 1000));
      }
    }
    
    // 모든 시도 실패 시 Mock 데이터 반환
    return this.getMockUSIndexData(indexCode);
  }

  // Mock 미국 지수 데이터 생성
  private getMockUSIndexData(indexCode: string): IndexData {
    const baseValues: Record<string, { name: string; value: number }> = {
      'S&P500': { name: 'S&P 500', value: 4500 },
      'DOW': { name: 'Dow Jones', value: 35000 },
      'NASDAQ': { name: 'NASDAQ', value: 14000 }
    };

    const baseData = baseValues[indexCode];
    if (!baseData) {
      throw new Error(`지원하지 않는 미국 지수: ${indexCode}`);
    }

    const change = Math.random() * 50 - 25; // -25 ~ +25
    const value = baseData.value + change;
    const changePct = (change / baseData.value) * 100;
    
    return {
      name: baseData.name,
      code: indexCode,
      value: Math.round(value * 100) / 100,
      change: Math.round(change * 100) / 100,
      change_pct: Math.round(changePct * 100) / 100,
      volume: Math.floor(Math.random() * 1000000000) + 100000000,
      timestamp: new Date().toISOString(),
    };
  }

  private toInt(value: any): number {
    try {
      return parseInt(String(value).trim()) || 0;
    } catch {
      return 0;
    }
  }

  private toFloat(value: any): number {
    try {
      return parseFloat(String(value).trim()) || 0.0;
    } catch {
      return 0.0;
    }
  }
}

// 시장 개장 상태 확인 함수들 (개선된 버전)
export function isKoreaMarketOpen(date?: Date): boolean {
  const now = date || new Date();
  const koreaTime = new Date(now.toLocaleString("en-US", { timeZone: "Asia/Seoul" }));
  
  // 주말 체크
  if (koreaTime.getDay() === 0 || koreaTime.getDay() === 6) {
    return false;
  }
  
  const hour = koreaTime.getHours();
  const minute = koreaTime.getMinutes();
  const time = hour * 100 + minute;
  
  // 한국장: 09:00 ~ 15:30 (평일)
  return time >= 900 && time <= 1530;
}

export function isUSMarketOpen(date?: Date): boolean {
  const now = date || new Date();
  const nyTime = new Date(now.toLocaleString("en-US", { timeZone: "America/New_York" }));
  
  // 주말 체크
  if (nyTime.getDay() === 0 || nyTime.getDay() === 6) {
    return false;
  }
  
  const hour = nyTime.getHours();
  const minute = nyTime.getMinutes();
  const time = hour * 100 + minute;
  
  // 미국장: 09:30 ~ 16:00 (평일)
  return time >= 930 && time <= 1600;
}

// 시장별 데이터 소스 결정 함수
export function getMarketDataSource(region: 'KR' | 'US'): 'websocket' | 'rest' {
  if (region === 'KR') {
    return isKoreaMarketOpen() ? 'websocket' : 'rest';
  } else {
    return isUSMarketOpen() ? 'websocket' : 'rest';
  }
}

// WebSocket TR ID 및 키 매핑
export const WEBSOCKET_CONFIG = {
  KR: {
    indices: {
      tr_id: 'H0STIDX0',
      keys: {
        'KOSPI': '0001',
        'KOSDAQ': '1001',
        'KOSPI200': '1002'
      }
    },
    stocks: {
      tr_id: 'H0STCNT0',
      // 종목 코드는 그대로 사용
    }
  },
  US: {
    indices: {
      tr_id: 'H0UHIDX0',
      keys: {
        'S&P500': 'NYS^INX',
        'DOW': 'NYS^DJI',
        'NASDAQ': 'NAS^IXIC'
      }
    },
    stocks: {
      tr_id: 'H0UHPHOG0',
      // 종목 코드는 그대로 사용
    }
  }
};

// REST API TR ID 매핑
export const REST_API_CONFIG = {
  KR: {
    indices: {
      tr_id: 'FHKIM04010100',
      endpoint: '/uapi/domestic-stock/v1/quotations/inquire-index'
    },
    stocks: {
      tr_id: 'FHKST01010100',
      endpoint: '/uapi/domestic-stock/v1/quotations/inquire-price'
    }
  },
  US: {
    indices: {
      tr_id: 'HHDFS76200200',
      endpoint: '/uapi/overseas-price/v1/quotations/price-detail'
    },
    stocks: {
      tr_id: 'HHDFS76200200',
      endpoint: '/uapi/overseas-price/v1/quotations/price-detail'
    }
  }
};

// 통합 헬퍼 함수들
export class MarketDataManager {
  private client: KoreaInvestClient;
  private wsConnected: boolean = false;
  private wsStockData: Record<string, StockData> = {};
  private wsIndexData: Record<string, IndexData> = {};

  constructor(client: KoreaInvestClient) {
    this.client = client;
  }

  // WebSocket 연결 상태 업데이트
  updateWebSocketStatus(connected: boolean, stockData?: Record<string, StockData>, indexData?: Record<string, IndexData>) {
    this.wsConnected = connected;
    if (stockData) this.wsStockData = stockData;
    if (indexData) this.wsIndexData = indexData;
    console.log(`WebSocket 상태 업데이트: 연결=${connected}, 주식=${Object.keys(stockData || {}).length}개, 지수=${Object.keys(indexData || {}).length}개`);
  }

  // 통합 지수 데이터 조회 (WebSocket/REST 자동 전환)
  async getIndexData(indexCode: string, region: 'KR' | 'US' = 'KR'): Promise<IndexData> {
    const dataSource = getMarketDataSource(region);
    const isOpen = region === 'KR' ? isKoreaMarketOpen() : isUSMarketOpen();
    
    console.log(`${indexCode} 지수 데이터 조회 (${region} 시장, ${dataSource} 소스, 개장=${isOpen}, WS연결=${this.wsConnected})`);

    // WebSocket이 연결되어 있고 시장이 열려있으면 WebSocket 데이터 사용
    if (dataSource === 'websocket' && this.wsConnected && isOpen) {
      const wsData = this.wsIndexData[indexCode];
      if (wsData && wsData.value > 0) {
        console.log(`${indexCode} WebSocket 실시간 데이터 사용`);
        return wsData;
      } else {
        console.log(`${indexCode} WebSocket 데이터 없음, REST API 사용`);
      }
    }

    // REST API 사용
    console.log(`${indexCode} REST API 데이터 사용`);
    return this.client.getIndexData(indexCode, region);
  }

  // 통합 주식 데이터 조회 (WebSocket/REST 자동 전환)
  async getStockData(symbol: string, region: 'KR' | 'US' = 'KR'): Promise<DomesticPrice | OverseasDetail> {
    const dataSource = getMarketDataSource(region);
    const isOpen = region === 'KR' ? isKoreaMarketOpen() : isUSMarketOpen();
    
    console.log(`${symbol} 주식 데이터 조회 (${region} 시장, ${dataSource} 소스, 개장=${isOpen}, WS연결=${this.wsConnected})`);

    // WebSocket이 연결되어 있고 시장이 열려있으면 WebSocket 데이터 사용
    if (dataSource === 'websocket' && this.wsConnected && isOpen) {
      const wsData = this.wsStockData[symbol];
      if (wsData && wsData.price > 0) {
        console.log(`${symbol} WebSocket 실시간 데이터 사용`);
        // WebSocket 데이터를 DomesticPrice/OverseasDetail 형식으로 변환
        if (region === 'KR') {
          return {
            symbol: wsData.symbol,
            price: wsData.price,
            change: wsData.change,
            change_pct: wsData.change_pct,
            volume: wsData.volume,
            timestamp: wsData.timestamp
          } as DomesticPrice;
        } else {
          return {
            symbol: wsData.symbol,
            market: 'US',
            last: wsData.price,
            change: wsData.change,
            change_pct: wsData.change_pct,
            open: 0,
            high: 0,
            low: 0,
            volume: wsData.volume,
            currency: 'USD',
            timestamp: wsData.timestamp
          } as OverseasDetail;
        }
      } else {
        console.log(`${symbol} WebSocket 데이터 없음, REST API 사용`);
      }
    }

    // REST API 사용
    console.log(`${symbol} REST API 데이터 사용`);
    if (region === 'KR') {
      return this.client.getDomesticPrice(symbol);
    } else {
      // 해외 주식은 EXCD와 SYMB를 분리해야 함
      const [excd, symb] = symbol.split(':');
      return this.client.getOverseasDetail(excd, symb);
    }
  }

  // 시장 상태 확인
  getMarketStatus(region: 'KR' | 'US'): {
    isOpen: boolean;
    dataSource: 'websocket' | 'rest';
    wsConnected: boolean;
  } {
    const isOpen = region === 'KR' ? isKoreaMarketOpen() : isUSMarketOpen();
    const dataSource = getMarketDataSource(region);
    
    return {
      isOpen,
      dataSource,
      wsConnected: this.wsConnected
    };
  }

  // WebSocket 데이터 직접 접근
  getWebSocketStockData(symbol: string): StockData | null {
    return this.wsStockData[symbol] || null;
  }

  getWebSocketIndexData(code: string): IndexData | null {
    return this.wsIndexData[code] || null;
  }

  // WebSocket 연결 상태 확인
  isWebSocketConnected(): boolean {
    return this.wsConnected;
  }
}

// 사용자별 API 키를 사용하는 클라이언트 생성 함수
export function createKoreaInvestClient(appkey: string, appsecret: string, mode: string = "prod"): KoreaInvestClient {
  if (!appkey || !appsecret) {
    throw new Error('한국투자증권 API 키가 설정되지 않았습니다.');
  }
  
  return new KoreaInvestClient(appkey, appsecret, mode);
}

// MarketDataManager를 포함한 통합 클라이언트 생성 함수
export function createMarketDataManager(appkey: string, appsecret: string, mode: string = "prod"): MarketDataManager {
  if (!appkey || !appsecret) {
    throw new Error('한국투자증권 API 키가 설정되지 않았습니다.');
  }
  
  const client = new KoreaInvestClient(appkey, appsecret, mode);
  return new MarketDataManager(client);
}

// 환경변수에서 API 키 가져오기 (기존 호환성 유지)
export function getKoreaInvestClient(): KoreaInvestClient {
  const appkey = process.env.NEXT_PUBLIC_KOREA_INVEST_APPKEY || '';
  const appsecret = process.env.NEXT_PUBLIC_KOREA_INVEST_APPSECRET || '';
  const mode = process.env.NEXT_PUBLIC_KOREA_INVEST_MODE || 'prod';
  
  if (!appkey || !appsecret) {
    throw new Error('한국투자증권 API 키가 설정되지 않았습니다. 환경변수를 확인해주세요.');
  }
  
  return new KoreaInvestClient(appkey, appsecret, mode);
}

// 환경변수에서 MarketDataManager 생성 (새로운 통합 방식)
export function getMarketDataManager(): MarketDataManager {
  const appkey = process.env.NEXT_PUBLIC_KOREA_INVEST_APPKEY || '';
  const appsecret = process.env.NEXT_PUBLIC_KOREA_INVEST_APPSECRET || '';
  const mode = process.env.NEXT_PUBLIC_KOREA_INVEST_MODE || 'prod';
  
  if (!appkey || !appsecret) {
    throw new Error('한국투자증권 API 키가 설정되지 않았습니다. 환경변수를 확인해주세요.');
  }
  
  const client = new KoreaInvestClient(appkey, appsecret, mode);
  return new MarketDataManager(client);
}

// DB에서 API 키를 가져와서 MarketDataManager 생성 (새로운 방식)
export async function getMarketDataManagerFromDB(): Promise<MarketDataManager> {
  try {
    // 로컬 스토리지에서 토큰 가져오기
    const accessToken = localStorage.getItem('accessToken') || localStorage.getItem('auth_token');
    
    if (!accessToken) {
      throw new Error('인증 토큰이 없습니다. 로그인이 필요합니다.');
    }

    // 사용자 세션에서 API 키 조회
    const response = await fetch('/api/account/api-keys', {
      method: 'GET',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${accessToken}`
      }
    });

    if (!response.ok) {
      if (response.status === 401) {
        throw new Error('인증이 만료되었습니다. 다시 로그인해주세요.');
      } else if (response.status === 404) {
        throw new Error('API 키가 설정되지 않았습니다. 설정 페이지에서 API 키를 등록해주세요.');
      } else {
        throw new Error(`API 키 조회 실패 (${response.status})`);
      }
    }

    const apiKeys = await response.json();
    
    if (!apiKeys.korea_investment_app_key || !apiKeys.korea_investment_app_secret) {
      throw new Error('한국투자증권 API 키가 설정되지 않았습니다. 설정 페이지에서 API 키를 등록해주세요.');
    }
    
    return createMarketDataManager(
      apiKeys.korea_investment_app_key,
      apiKeys.korea_investment_app_secret,
      'prod'
    );
  } catch (error) {
    console.error('DB에서 API 키 조회 실패:', error);
    throw error; // 원본 오류 메시지 유지
  }
} 