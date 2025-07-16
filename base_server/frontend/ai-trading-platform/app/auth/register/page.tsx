"use client"

import type React from "react"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Alert, AlertDescription } from "@/components/ui/alert"
import { Loader2, TrendingUp, Zap, Check } from "lucide-react"
import { authApi } from "@/lib/api/auth"

export default function RegisterPage() {
  const [formData, setFormData] = useState({
    name: "",
    email: "",
    password: "",
    confirmPassword: "",
  })
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)

  const router = useRouter()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")

    if (formData.password !== formData.confirmPassword) {
      setError("비밀번호가 일치하지 않습니다.")
      return
    }

    if (formData.password.length < 6) {
      setError("비밀번호는 최소 6자 이상이어야 합니다.")
      return
    }

    setIsLoading(true)

    try {
      await authApi.register({
        name: formData.name,
        email: formData.email,
        password: formData.password,
      })

      router.push("/auth/login?message=회원가입이 완료되었습니다. 로그인해주세요.")
    } catch (err) {
      setError("회원가입에 실패했습니다. 다시 시도해주세요.")
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setFormData((prev) => ({
      ...prev,
      [e.target.name]: e.target.value,
    }))
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
        {/* Register Form */}
        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: 24 }}>
            <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>이름</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleInputChange}
              required
              placeholder="홍길동"
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
            <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>이메일</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleInputChange}
              required
              placeholder="example@email.com"
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
              name="password"
              value={formData.password}
              onChange={handleInputChange}
              required
              placeholder="최소 6자 이상"
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
            <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>비밀번호 확인</label>
            <input
              type="password"
              name="confirmPassword"
              value={formData.confirmPassword}
              onChange={handleInputChange}
              required
              placeholder="비밀번호를 다시 입력하세요"
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
                가입 중...
              </>
            ) : (
              "회원가입"
            )}
          </button>
          <div style={{ textAlign: "center", fontSize: 14, color: "#a5b4fc" }}>
            <span>이미 계정이 있으신가요? </span>
            <Link href="/auth/login" style={{ color: "#67e8f9", fontWeight: 500 }}>로그인</Link>
          </div>
        </form>
      </div>
    </div>
  )
}
