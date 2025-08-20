import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { accessToken, market = "NASDAQ", strategy = "MOMENTUM" } = body || {}

    if (!accessToken) {
      return NextResponse.json({ error: "사용자 accessToken 없음" }, { status: 401 })
    }

    const backend = process.env.NEXT_PUBLIC_API_URL ?? "https://bullant-kr.com"
    const res = await fetch(`${backend}/api/dashboard/stock/recommendation`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ accessToken, market, strategy })
    })

    const text = await res.text()
    if (!res.ok) {
      return NextResponse.json({ error: text || "backend error" }, { status: res.status })
    }

    // 백엔드 응답이 문자열(JSON 직렬화)일 수 있어 파싱 시도
    let data: any
    try { data = JSON.parse(text) } catch { data = text }

    // 이중 직렬화 케이스 방어: 문자열로 한 번 더 감싸져 온 경우
    if (typeof data === "string") {
      try { data = JSON.parse(data) } catch { /* keep as-is */ }
    }

    return NextResponse.json(data)
  } catch (err) {
    console.error("/api/dashboard/stock/recommendation error", err)
    return NextResponse.json({ error: "route error" }, { status: 500 })
  }
}


