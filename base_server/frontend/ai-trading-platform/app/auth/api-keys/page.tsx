"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Key, SkipForward, Save, AlertCircle } from "lucide-react";

export default function ApiKeysPage() {
  const router = useRouter();
  const [apiKeys, setApiKeys] = useState({
    korea_investment_app_key: "",
    korea_investment_app_secret: "",
    alpha_vantage_key: "",
    polygon_key: "",
    finnhub_key: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // 토큰 확인
    if (typeof window !== "undefined") {
      const accessToken = localStorage.getItem("accessToken");
      if (!accessToken) {
        window.location.href = "/auth/login";
      }
    }
  }, []);

  const handleInputChange = (key: string, value: string) => {
    setApiKeys(prev => ({ ...prev, [key]: value }));
  };

  const handleSave = async () => {
    setIsLoading(true);
    setError("");
    
    try {
      // API 키 저장 로직 (백엔드 API 호출)
      // 실제로는 백엔드에 API 키를 저장하는 엔드포인트가 필요합니다
      console.log("저장할 API 키:", apiKeys);
      
      // 임시로 1초 대기 (실제 API 호출로 대체)
      await new Promise(resolve => setTimeout(resolve, 1000));
      
      // 성공 시 온보딩으로 이동
      window.location.href = "/onboarding";
    } catch (err: any) {
      setError("API 키 저장에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    // 건너뛰기 시 온보딩으로 이동
    window.location.href = "/onboarding";
  };

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
          maxWidth: 600,
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
        {/* Header */}
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: 12, marginBottom: 16 }}>
            <div style={{ width: 48, height: 48, background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)", borderRadius: 12, display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 4px 16px #667eea33" }}>
              <Key style={{ width: 28, height: 28, color: "#fff" }} />
            </div>
          </div>
          <h1 style={{ fontSize: 24, fontWeight: 700, color: "#fff", marginBottom: 8 }}>API 키 설정</h1>
          <p style={{ fontSize: 14, color: "rgba(255,255,255,0.6)" }}>
            더 정확한 투자 정보를 위해 API 키를 입력해 주세요. 나중에 설정에서도 변경할 수 있습니다.
          </p>
        </div>

        {/* API Keys Form */}
        <div style={{ marginBottom: 32 }}>
          {/* 한국투자증권 API */}
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 12 }}>한국투자증권 API</h3>
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 12 }}>
              <div>
                <label style={{ color: "rgba(255,255,255,0.8)", fontSize: 14, marginBottom: 6, display: "block" }}>App Key</label>
                <input
                  type="password"
                  value={apiKeys.korea_investment_app_key}
                  onChange={e => handleInputChange("korea_investment_app_key", e.target.value)}
                  placeholder="한국투자증권 App Key"
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    borderRadius: 8,
                    background: "rgba(30,35,50,0.95)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    color: "#fff",
                    fontSize: 14,
                    outline: "none",
                    transition: "border 0.2s",
                  }}
                />
              </div>
              <div>
                <label style={{ color: "rgba(255,255,255,0.8)", fontSize: 14, marginBottom: 6, display: "block" }}>App Secret</label>
                <input
                  type="password"
                  value={apiKeys.korea_investment_app_secret}
                  onChange={e => handleInputChange("korea_investment_app_secret", e.target.value)}
                  placeholder="한국투자증권 App Secret"
                  style={{
                    width: "100%",
                    padding: "12px 16px",
                    borderRadius: 8,
                    background: "rgba(30,35,50,0.95)",
                    border: "1px solid rgba(255,255,255,0.12)",
                    color: "#fff",
                    fontSize: 14,
                    outline: "none",
                    transition: "border 0.2s",
                  }}
                />
              </div>
            </div>
          </div>

          {/* Alpha Vantage API */}
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 12 }}>Alpha Vantage API</h3>
            <input
              type="password"
              value={apiKeys.alpha_vantage_key}
              onChange={e => handleInputChange("alpha_vantage_key", e.target.value)}
              placeholder="Alpha Vantage API Key"
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: 8,
                background: "rgba(30,35,50,0.95)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#fff",
                fontSize: 14,
                outline: "none",
                transition: "border 0.2s",
              }}
            />
          </div>

          {/* Polygon API */}
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 12 }}>Polygon API</h3>
            <input
              type="password"
              value={apiKeys.polygon_key}
              onChange={e => handleInputChange("polygon_key", e.target.value)}
              placeholder="Polygon API Key"
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: 8,
                background: "rgba(30,35,50,0.95)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#fff",
                fontSize: 14,
                outline: "none",
                transition: "border 0.2s",
              }}
            />
          </div>

          {/* Finnhub API */}
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 12 }}>Finnhub API</h3>
            <input
              type="password"
              value={apiKeys.finnhub_key}
              onChange={e => handleInputChange("finnhub_key", e.target.value)}
              placeholder="Finnhub API Key"
              style={{
                width: "100%",
                padding: "12px 16px",
                borderRadius: 8,
                background: "rgba(30,35,50,0.95)",
                border: "1px solid rgba(255,255,255,0.12)",
                color: "#fff",
                fontSize: 14,
                outline: "none",
                transition: "border 0.2s",
              }}
            />
          </div>
        </div>

        {/* Error Message */}
        {error && (
          <div style={{ 
            display: "flex", 
            alignItems: "center", 
            gap: 8, 
            padding: "12px 16px", 
            background: "rgba(239, 68, 68, 0.1)", 
            border: "1px solid rgba(239, 68, 68, 0.3)", 
            borderRadius: 8, 
            marginBottom: 24,
            color: "#ef4444"
          }}>
            <AlertCircle size={16} />
            <span style={{ fontSize: 14 }}>{error}</span>
          </div>
        )}

        {/* Action Buttons */}
        <div style={{ display: "flex", gap: 12 }}>
          <button
            type="button"
            onClick={handleSkip}
            style={{
              flex: 1,
              padding: "14px 20px",
              borderRadius: 8,
              background: "rgba(255,255,255,0.05)",
              border: "1px solid rgba(255,255,255,0.1)",
              color: "rgba(255,255,255,0.7)",
              fontSize: 15,
              fontWeight: 500,
              cursor: "pointer",
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
            }}
            onMouseEnter={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.1)";
              e.currentTarget.style.color = "#fff";
            }}
            onMouseLeave={(e) => {
              e.currentTarget.style.background = "rgba(255,255,255,0.05)";
              e.currentTarget.style.color = "rgba(255,255,255,0.7)";
            }}
          >
            <SkipForward size={16} />
            나중에 설정
          </button>
          <button
            type="button"
            onClick={handleSave}
            disabled={isLoading}
            style={{
              flex: 1,
              padding: "14px 20px",
              borderRadius: 8,
              background: "linear-gradient(135deg, #667eea 0%, #764ba2 100%)",
              border: "none",
              color: "#fff",
              fontSize: 15,
              fontWeight: 500,
              cursor: isLoading ? "not-allowed" : "pointer",
              transition: "all 0.2s",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              gap: 8,
              opacity: isLoading ? 0.6 : 1,
            }}
            onMouseEnter={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = "translateY(-1px)";
                e.currentTarget.style.boxShadow = "0 4px 12px rgba(102, 126, 234, 0.4)";
              }
            }}
            onMouseLeave={(e) => {
              if (!isLoading) {
                e.currentTarget.style.transform = "translateY(0)";
                e.currentTarget.style.boxShadow = "none";
              }
            }}
          >
            {isLoading ? (
              <div style={{ width: 16, height: 16, border: "2px solid transparent", borderTop: "2px solid #fff", borderRadius: "50%", animation: "spin 1s linear infinite" }} />
            ) : (
              <Save size={16} />
            )}
            {isLoading ? "저장 중..." : "저장하고 계속"}
          </button>
        </div>

        {/* Info Box */}
        <div
          style={{
            marginTop: 24,
            padding: 16,
            background: "linear-gradient(135deg, rgba(59, 130, 246, 0.1) 0%, rgba(147, 51, 234, 0.1) 100%)",
            borderRadius: 12,
            border: "1px solid rgba(59, 130, 246, 0.2)",
            color: "rgba(255,255,255,0.8)",
            fontSize: 13,
          }}
        >
          <div style={{ fontWeight: 600, marginBottom: 4 }}>💡 API 키가 필요한 이유</div>
          <div style={{ lineHeight: 1.5 }}>
            • 한국투자증권: 실시간 주식 데이터 및 거래 기능<br/>
            • Alpha Vantage: 글로벌 주식 시장 데이터<br/>
            • Polygon: 실시간 시장 데이터 및 뉴스<br/>
            • Finnhub: 금융 데이터 및 뉴스 피드
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
} 