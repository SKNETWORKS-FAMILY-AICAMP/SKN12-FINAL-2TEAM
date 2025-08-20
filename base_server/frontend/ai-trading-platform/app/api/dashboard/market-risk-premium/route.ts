import { NextRequest, NextResponse } from "next/server"

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { accessToken, countries = ["US", "KR", "JP", "CN", "EU"] } = body || {}

    if (!accessToken) {
      return NextResponse.json({ error: "사용자 accessToken 없음" }, { status: 401 })
    }

    // 실제 백엔드 API 호출
    const backend = process.env.NEXT_PUBLIC_API_URL ?? "https://bullant-kr.com"
    console.log("🌐 백엔드 API 호출:", `${backend}/api/dashboard/market-risk-premium`)
    
    try {
      const res = await fetch(`${backend}/api/dashboard/market-risk-premium`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ accessToken, countries })
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
        premiums: [
          {
            country: "미국",
            countryCode: "US",
            continent: "North America",
            countryRiskPremium: 0.0,
            totalEquityRiskPremium: 4.6
          },
          {
            country: "한국",
            countryCode: "KR",
            continent: "Asia",
            countryRiskPremium: 1.2,
            totalEquityRiskPremium: 5.8
          },
          {
            country: "일본",
            countryCode: "JP",
            continent: "Asia",
            countryRiskPremium: 0.8,
            totalEquityRiskPremium: 5.4
          },
          {
            country: "중국",
            countryCode: "CN",
            continent: "Asia",
            countryRiskPremium: 1.5,
            totalEquityRiskPremium: 6.1
          },
          {
            country: "유럽연합",
            countryCode: "EU",
            continent: "Europe",
            countryRiskPremium: 0.5,
            totalEquityRiskPremium: 5.1
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
    console.error("/api/dashboard/market-risk-premium error", err)
    return NextResponse.json({ error: "route error" }, { status: 500 })
  }
}
