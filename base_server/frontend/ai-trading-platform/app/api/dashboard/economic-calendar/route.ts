import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { accessToken, days = 7 } = body || {}

    if (!accessToken) {
      return NextResponse.json({ error: "사용자 accessToken 없음" }, { status: 401 })
    }

    // 실제 백엔드 API 호출
    const backend = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
    console.log("🌐 백엔드 API 호출:", `${backend}/api/dashboard/economic-calendar`)
    
    try {
      const res = await fetch(`${backend}/api/dashboard/economic-calendar`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accessToken, days })
      })

      const text = await res.text()
      console.log("📥 백엔드 응답 상태:", res.status)
      console.log("📥 백엔드 응답:", text)

      if (res.ok) {
        // 백엔드 응답 처리
        let data: any
        
        try {
          // 먼저 JSON 파싱 시도
          data = JSON.parse(text)
          console.log("✅ JSON 파싱 성공:", typeof data)
        } catch (parseError) {
          console.warn("⚠️ JSON 파싱 실패, 원본 텍스트 사용:", parseError)
          data = text
        }

        // 이중 직렬화 케이스 방어: 문자열로 한 번 더 감싸져 온 경우
        if (typeof data === "string") {
          try {
            const parsed = JSON.parse(data)
            if (typeof parsed === "object" && parsed !== null) {
              data = parsed
              console.log("✅ 이중 직렬화 해제 성공")
            }
          } catch (doubleParseError) {
            console.warn("⚠️ 이중 직렬화 해제 실패:", doubleParseError)
            // 원본 문자열 그대로 사용
          }
        }

        console.log("✅ 백엔드 API 성공:", data)
        return NextResponse.json(data)
      } else {
        console.warn("⚠️ 백엔드 API 실패, 더미 데이터 반환")
        throw new Error(`백엔드 API 실패: ${res.status} ${text}`)
      }
    } catch (apiError) {
      console.error("🔥 백엔드 API 호출 실패:", apiError)
      
      // API 실패 시 더미 데이터 반환
      const dummyData = {
        result: "success",
        events: [
          {
            date: "12월 18일",
            time: "09:30",
            country: "미국",
            event: "비농업 고용지표",
            impact: "High",
            previous: "187K",
            forecast: "180K",
            actual: null,
            currency: "USD",
            change: "N/A",
            changePercentage: "N/A"
          },
          {
            date: "12월 19일",
            time: "14:00",
            country: "미국",
            event: "ISM 제조업 지수",
            impact: "Medium",
            previous: "49.0",
            forecast: "49.5",
            actual: null,
            currency: "USD",
            change: "N/A",
            changePercentage: "N/A"
          },
          {
            date: "12월 20일",
            time: "09:30",
            country: "미국",
            event: "소비자 물가지수(CPI)",
            impact: "High",
            previous: "3.2%",
            forecast: "3.1%",
            actual: null,
            currency: "USD",
            change: "N/A",
            changePercentage: "N/A"
          },
          {
            date: "12월 21일",
            time: "14:00",
            country: "미국",
            event: "연방기금 금리",
            impact: "High",
            previous: "5.50%",
            forecast: "5.50%",
            actual: null,
            currency: "USD",
            change: "N/A",
            changePercentage: "N/A"
          },
          {
            date: "12월 22일",
            time: "09:30",
            country: "미국",
            event: "소매 판매",
            impact: "Medium",
            previous: "0.3%",
            forecast: "0.2%",
            actual: null,
            currency: "USD",
            change: "N/A",
            changePercentage: "N/A"
          }
        ],
        message: "API 오류로 인해 더미 데이터를 반환합니다",
        source: "더미 데이터 (API 실패)",
        errorCode: 1000
      }

      console.log("📤 더미 데이터 반환:", dummyData)
      return NextResponse.json(dummyData)
    }
  } catch (err) {
    console.error("/api/dashboard/economic-calendar error", err)
    return NextResponse.json({ error: "route error" }, { status: 500 })
  }
}

