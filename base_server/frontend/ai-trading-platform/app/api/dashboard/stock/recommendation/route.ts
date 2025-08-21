import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { accessToken, market = "NASDAQ", strategy = "MOMENTUM" } = body || {}

    if (!accessToken) {
      return NextResponse.json({ error: "사용자 accessToken 없음" }, { status: 401 })
    }

    const backend = process.env.NEXT_PUBLIC_API_URL ?? "https://bullant-kr.com"
    
    // 서버 환경을 위한 긴 타임아웃 설정
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 120000); // 120초 타임아웃
    
    const res = await fetch(`${backend}/api/dashboard/stock/recommendation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ accessToken, market, strategy }),
      signal: controller.signal
    });
    
    clearTimeout(timeoutId);

    const text = await res.text()
    if (!res.ok) {
      return NextResponse.json({ error: text || "backend error" }, { status: res.status })
    }

    // 디버깅을 위한 로그 추가
    console.log("🔍 [API Route] 백엔드 원본 응답:", text);
    console.log("🔍 [API Route] 응답 길이:", text.length);

    // 백엔드 응답이 문자열(JSON 직렬화)일 수 있어 파싱 시도
    let data: any
    try { 
      data = JSON.parse(text) 
      console.log("🔍 [API Route] JSON 파싱 성공:", typeof data);
    } catch (e) { 
      console.log("🔍 [API Route] JSON 파싱 실패, 원본 텍스트 반환");
      data = text 
    }

    // 이중 직렬화 케이스 방어: 문자열로 한 번 더 감싸져 온 경우
    if (typeof data === "string") {
      try { 
        const parsed = JSON.parse(data)
        console.log("🔍 [API Route] 이중 JSON 파싱 성공:", typeof parsed);
        data = parsed
      } catch (e) { 
        console.log("🔍 [API Route] 이중 JSON 파싱 실패, 원본 유지");
        // keep as-is 
      }
    }

    console.log("🔍 [API Route] 최종 반환 데이터:", data);
    return NextResponse.json(data)
  } catch (err) {
    console.error("/api/dashboard/stock/recommendation error", err)
    // 타임아웃 에러 구분
    if (err instanceof Error && err.name === 'AbortError') {
      return NextResponse.json({ error: "백엔드 응답 타임아웃 (120초 초과)" }, { status: 504 })
    }
    return NextResponse.json({ error: "route error" }, { status: 500 })
  }
}


