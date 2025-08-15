import { NextRequest, NextResponse } from "next/server"

// 프록시 큐: 초당 제한(EGW00201) 회피를 위해 200ms 간격 디스패치
type Task = {
  body: any
  resolve: (v: NextResponse) => void
  reject: (e?: any) => void
  retries: number
}

const queue: Task[] = []
let timer: ReturnType<typeof setTimeout> | null = null

function start() {
  if (timer) return
  const dispatch = async () => {
    if (queue.length === 0) { timer && clearTimeout(timer); timer = null; return }
    const t = queue.shift()!
    try {
      const backend = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000"
      const res = await fetch(`${backend}/api/dashboard/price/us`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(t.body)
      })

      const text = await res.text()
      if (!res.ok) {
        // 초당 거래건수 초과 시 지터 재시도 (최대 2회)
        if (text?.includes("EGW00201") && t.retries < 2) {
          t.retries += 1
          const jitter = 400 + Math.floor(Math.random() * 800)
          setTimeout(() => { queue.push(t); start() }, jitter)
        } else {
          // 에러도 JSON으로 래핑하여 클라이언트 파싱 안정화
          let payload: any = text
          try { payload = JSON.parse(text) } catch {}
          t.resolve(NextResponse.json({ error: payload, status: res.status }, { status: res.status }))
        }
      } else {
        let data: any
        try { data = JSON.parse(text) } catch { data = text }
        if (typeof data === "string") { try { data = JSON.parse(data) } catch {} }
        t.resolve(NextResponse.json(data))
      }
    } catch (e) {
      t.reject(e)
    } finally {
      timer = setTimeout(dispatch, 200) // ≈ 5 req/s
    }
  }
  timer = setTimeout(dispatch, 0)
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    if (!body || !body.ticker) {
      return NextResponse.json({ error: "ticker required" }, { status: 400 })
    }
    return await new Promise<NextResponse>((resolve, reject) => {
      queue.push({ body, resolve, reject, retries: 0 })
      start()
    })
  } catch (e) {
    return NextResponse.json({ error: "route error" }, { status: 500 })
  }
}


