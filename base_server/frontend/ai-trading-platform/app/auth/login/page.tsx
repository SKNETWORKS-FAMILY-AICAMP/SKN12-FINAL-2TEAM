"use client";

import type React from "react"
import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Loader2, TrendingUp, Zap } from "lucide-react"
import { useAuth } from "@/hooks/use-auth"
import axios from "axios"

export default function LoginPage() {
  const [accountId, setAccountId] = useState("")
  const [password, setPassword] = useState("demo123")
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const { login } = useAuth()
  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setIsLoading(true)

    try {
      // payload 생성 및 콘솔 출력
      const payload = {
        platform_type: 1, // int로 고정
        account_id: accountId,
        password: password,
      };
      console.log("로그인 요청 payload:", payload);

      const res = await axios.post("http://127.0.0.1:8000/api/account/login", payload);
      let data = res.data;
      if (typeof data === "string") {
        try {
          data = JSON.parse(data);
        } catch (parseErr) {
          console.error("로그인 응답 파싱 에러:", parseErr, data);
          setError("서버 응답 파싱 오류가 발생했습니다.");
          setIsLoading(false);
          return;
        }
      }
      console.log('로그인 응답:', data);
      if (data.errorCode === 0 || data.errorCode === "0") {
        // accessToken, refreshToken, user_id 저장
        if (data.accessToken) localStorage.setItem('accessToken', data.accessToken)
        if (data.refreshToken) localStorage.setItem('refreshToken', data.refreshToken)
        if (data.user_id) localStorage.setItem('userId', data.user_id)
        router.push("/onboarding")
        return;
      } else {
        const errorCode = data.errorCode;
        const message = data.message;
        console.log('로그인 실패 errorCode:', errorCode, 'message:', message);
        setError(message || `로그인 실패: 에러코드 ${errorCode}`);
      }
    } catch (err: any) {
      console.error("로그인 에러:", err);
      const errorCode = err?.response?.data?.errorCode;
      const message = err?.response?.data?.message;
      setError(message || "네트워크 오류가 발생했습니다.");
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div
      style={{
        minHeight: "100vh",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        background:
          `radial-gradient(circle at 20% 80%, rgba(0, 100, 200, 0.1) 0%, transparent 50%),\n` +
          `radial-gradient(circle at 80% 20%, rgba(255, 255, 255, 0.05) 0%, transparent 50%),\n` +
          `radial-gradient(circle at 40% 40%, rgba(0, 50, 150, 0.08) 0%, transparent 50%),\n` +
          `linear-gradient(135deg, #0a0a0a 0%, #111111 25%, #0d0d0d 50%, #121212 75%, #0a0a0a 100%)`,
        backgroundSize: "100% 100%, 100% 100%, 100% 100%, 100% 100%",
        backgroundAttachment: "fixed",
        color: "#fff",
      }}
    >
      <div
        style={{
          width: "100%",
          maxWidth: 420,
          background:
            "linear-gradient(135deg, rgba(102, 126, 234, 0.08) 0%, rgba(118, 75, 162, 0.08) 100%)," +
            "linear-gradient(45deg, rgba(255, 255, 255, 0.02) 0%, transparent 50%)",
          borderRadius: 20,
          padding: 36,
          border: "1px solid rgba(255,255,255,0.08)",
          backdropFilter: "blur(20px)",
          boxShadow:
            "0 20px 40px rgba(0,0,0,0.3), inset 0 1px 0 rgba(255,255,255,0.05)",
        }}
      >
        {/* Logo */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 12, marginBottom: 16 }}>
            <div style={{ position: "relative" }}>
              <div style={{ width: 48, height: 48, background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 16px #667eea33" }}>
                <TrendingUp style={{ width: 28, height: 28, color: "#fff" }} />
              </div>
              <div style={{ position: "absolute", top: -8, right: -8, width: 24, height: 24, background: "linear-gradient(135deg, #fbbf24 0%, #f59e42 100%)", borderRadius: 999, display: "flex", alignItems: "center", justifyContent: "center" }}>
                <Zap style={{ width: 14, height: 14, color: "#fff" }} />
              </div>
            </div>
            <div>
              <h1 style={{ fontSize: 24, fontWeight: 700, background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", WebkitBackgroundClip: "text", WebkitTextFillColor: "transparent", backgroundClip: "text" }}>AI Trader Pro</h1>
              <p style={{ fontSize: 14, color: "rgba(255,255,255,0.6)" }}>Professional Trading Platform</p>
            </div>
          </div>
        </div>
        {/* Login Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 24 }}>
            <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>아이디</label>
            <input
              type="text"
              value={accountId}
              onChange={e => setAccountId(e.target.value)}
              required
              placeholder="아이디"
              style={{
                width: "100%",
                padding: "14px 16px",
                borderRadius: 8,
                background: "rgba(30,35,50,0.95)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#fff",
                fontSize: 15,
                marginBottom: 8,
                outline: "none",
                boxShadow: "none",
                transition: "border 0.2s",
              }}
            />
          </div>
          <div style={{ marginBottom: 24 }}>
            <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>비밀번호</label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              required
              placeholder="비밀번호"
              style={{
                width: "100%",
                padding: "14px 16px",
                borderRadius: 8,
                background: "rgba(30,35,50,0.95)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#fff",
                fontSize: 15,
                marginBottom: 8,
                outline: "none",
                boxShadow: "none",
                transition: "border 0.2s",
              }}
            />
          </div>
          {error && <div style={{ color: "#f87171", fontSize: 14, marginBottom: 12 }}>{error}</div>}
          <button
            type="submit"
            disabled={isLoading}
            style={{
              width: "100%",
              padding: "16px 0",
              borderRadius: 8,
              fontWeight: 700,
              fontSize: 16,
              background: isLoading ? "rgba(255,255,255,0.05)" : "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
              color: isLoading ? "#888" : "#fff",
              border: "none",
              cursor: isLoading ? "not-allowed" : "pointer",
              boxShadow: isLoading ? "none" : "0 2px 12px #667eea33",
              marginBottom: 16,
              transition: "all 0.2s",
            }}
          >
            {isLoading ? (
              <>
                <Loader2 style={{ marginRight: 8, width: 18, height: 18, verticalAlign: "middle", display: "inline-block" }} className="animate-spin" />
                로그인 중...
              </>
            ) : (
              "로그인"
            )}
          </button>
          <div style={{ textAlign: "center", fontSize: 14, color: "#a5b4fc" }}>
            <span>계정이 없으신가요? </span>
            <Link href="/auth/register" style={{ color: "#67e8f9", fontWeight: 500 }}>회원가입</Link>
          </div>
        </form>
        {/* Demo Credentials */}
        <div
          style={{
            marginTop: 32,
            padding: 18,
            background: "linear-gradient(135deg, rgba(255,255,255,0.03) 0%, rgba(255,255,255,0.01) 100%),linear-gradient(45deg, rgba(102,126,234,0.05) 0%, transparent 50%)",
            borderRadius: 12,
            border: "1px solid rgba(255,255,255,0.06)",
            backdropFilter: "blur(15px)",
            color: "#a5b4fc",
            fontSize: 14,
            marginBottom: 0,
          }}
        >
          <div style={{ fontWeight: 600, color: "#a5b4fc", marginBottom: 6 }}>데모 계정</div>
          <div style={{ fontSize: 13, color: "#c7d2fe" }}>
            <div>이메일: demo@example.com</div>
            <div>비밀번호: demo123</div>
          </div>
        </div>
      </div>
    </div>
  )
}
