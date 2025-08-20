import { NextRequest, NextResponse } from "next/server"

/* ──────────────────────────────────────────
   글로벌 캐시 (람다/Edge 재사용 시 살아있음)
──────────────────────────────────────────── */
let cachedToken:  string | null = null
let cachedAppKey: string | null = null
let cachedUntil  = 0                          // ms epoch
let inFlight: Promise<void> | null = null

export async function POST(request: NextRequest) {
  try {
    console.log("들어왔습니다. 인증하러")
    
    /* 1. 바디에서 사용자 accessToken 확인 */
    const body = await request.json()
    const accessToken = body.accessToken
    
    if (!accessToken) {
      return NextResponse.json(
        { error: "사용자 토큰 없음" },
        { status: 401 }
      )
    }

    /* 2. 캐시가 유효(55분 TTL)하면 즉시 반환 */
    if (cachedToken && Date.now() < cachedUntil) {
      console.log("[OAuth] 캐시 hit")
      return NextResponse.json({
        access_token: cachedToken,
        app_key     : cachedAppKey,
      })
    }

    /* 3. 동시에 여러 요청이 들어오면 inFlight 로 직렬화 */
    if (inFlight) {
      await inFlight
      return NextResponse.json({
        access_token: cachedToken,
        app_key     : cachedAppKey,
      })
    }

    /* 4. 새 발급 루틴 시작 */
    inFlight = (async () => {
      const backend =
        process.env.NEXT_PUBLIC_API_URL ?? "https://bullant-kr.com"

      const res = await fetch(`${backend}/api/dashboard/oauth`, {
        method : "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({ 
          accessToken: accessToken,
          mode: "prod" 
        }),
      })

      /* 4-1) HTTP 오류 → 캐시 폴백 (예외로 500 발생 방지) */
      if (!res.ok) {
        const errText = await res.text().catch(() => "")
        console.error("[OAuth] backend HTTP error", res.status, errText)
        // 캐시가 살아 있으면 그대로 사용, 아니면 종료 (상위에서 캐시 반환)
        return
      }

      /* 4-2) 본문 파싱 후 업무 코드 검사 (문자/객체 모두 안전 파싱) */
      const rawText = await res.text()
      let ss: any
      try { ss = JSON.parse(rawText) } catch { ss = rawText }
      if (typeof ss === 'string') {
        try { ss = JSON.parse(ss) } catch { ss = {} }
      }
      console.log("[OAuth] backend response:", ss)

      if (ss.errorCode !== 0 || ss.result === "fail") {
        console.warn("[OAuth] backend biz fail", ss.errorCode, ss.message)
        // 캐시가 살아 있으면 그것을 그대로 사용
        if (cachedToken && Date.now() < cachedUntil) return
        // 최소한 app_key 기반으로라도 클라이언트가 진행할 수 있게 폴백 저장
        cachedToken  = ss.access_token ?? ss.app_key ?? null
        cachedAppKey = ss.app_key ?? ss.access_token ?? null
        cachedUntil  = Date.now() + 10 * 60 * 1000 // 10분 폴백 TTL
        return
      }

      /* 4-3) 정상 ⇒ 캐시 갱신 */
      cachedToken  = ss.access_token ?? null
      cachedAppKey = ss.app_key ?? ss.access_token ?? null
      cachedUntil  = Date.now() + 55 * 60 * 1000   // 55 min TTL
      console.log("[OAuth] 발급 성공·캐시 저장")
    })()

    /* 5. 발급 루틴 완료 대기 */
    await inFlight
    return NextResponse.json({
      access_token: cachedToken,
      app_key     : cachedAppKey,
    })
  } catch (err) {
    console.error("🔥 OAuth route error:", err)
    return NextResponse.json(
      { error: "OAuth 인증 실패" },
      { status: 500 }
    )
  } finally {
    inFlight = null       // 잠금 해제
  }
}
