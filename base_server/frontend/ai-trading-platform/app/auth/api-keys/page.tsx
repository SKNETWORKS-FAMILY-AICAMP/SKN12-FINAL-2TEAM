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
        router.push("/auth/login");
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
      // 실제 백엔드 API 호출
      const apiBase = process.env.NEXT_PUBLIC_API_URL;
      if (!apiBase) throw new Error("NEXT_PUBLIC_API_URL 환경변수가 필요합니다");
      
      const response = await fetch(`${apiBase}/api/account/api-keys/save`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${localStorage.getItem('accessToken')}`
        },
        body: JSON.stringify({
          korea_investment_app_key: apiKeys.korea_investment_app_key,
          korea_investment_app_secret: apiKeys.korea_investment_app_secret,
          alpha_vantage_key: apiKeys.alpha_vantage_key,
          polygon_key: apiKeys.polygon_key,
          finnhub_key: apiKeys.finnhub_key,
          accessToken: localStorage.getItem('accessToken'),
          sequence: Date.now()
        })
      });

      console.log("Response status:", response.status);
      console.log("Response ok:", response.ok);
      
      const responseText = await response.text();
      console.log("응답 텍스트:", responseText);
      
      let data;
      try {
        // 첫 번째 파싱 시도
        data = JSON.parse(responseText);
        console.log("첫 번째 파싱 결과:", data);
        
        // 만약 여전히 문자열이면 두 번째 파싱 시도 (이중 인코딩 처리)
        if (typeof data === 'string') {
          console.log("이중 인코딩 감지, 두 번째 파싱 시도");
          data = JSON.parse(data);
          console.log("두 번째 파싱 결과:", data);
        }
      } catch (parseError) {
        console.error("JSON 파싱 오류:", parseError);
        console.error("파싱 실패한 텍스트:", responseText);
        setError("서버 응답을 처리할 수 없습니다.");
        return;
      }
      
      // 배열인 경우 첫 번째 요소 추출
      console.log("파싱된 데이터 타입:", typeof data);
      console.log("파싱된 데이터가 배열인가?", Array.isArray(data));
      console.log("파싱된 데이터:", data);
      
      if (Array.isArray(data)) {
        console.log("배열에서 첫 번째 요소 추출 전:", data);
        data = data[0];
        console.log("배열에서 첫 번째 요소 추출 후:", data);
      }
      
      console.log("최종 데이터:", data);
      console.log("errorCode 타입:", typeof data.errorCode);
      console.log("errorCode 값:", data.errorCode);
      console.log("응답 전체 내용:", JSON.stringify(data, null, 2));
      
      // 안전장치: data가 유효한지 확인
      if (!data || typeof data !== 'object') {
        console.error("유효하지 않은 데이터:", data);
        setError("서버 응답이 올바르지 않습니다.");
        return;
      }
      
      if (data.errorCode === 0 || data.errorCode === "0") {
        // 성공 시 온보딩으로 이동
        console.log("API 키 저장 성공, 온보딩으로 이동");
        // 강제 새로고침으로 캐시 문제 해결
        window.location.replace("/onboarding");
      } else {
        console.log("API 키 저장 실패:", data.message)
        setError(data.message || "API 키 저장에 실패했습니다.");
      }
    } catch (err: any) {
      console.error("API 키 저장 에러:", err);
      
      // 더 구체적인 에러 메시지 제공
      if (err.message?.includes("NEXT_PUBLIC_API_URL")) {
        setError("환경 설정 오류입니다. 관리자에게 문의해주세요.");
      } else if (err.message?.includes("fetch")) {
        setError("서버 연결에 실패했습니다. 백엔드 서버가 실행 중인지 확인해주세요.");
      } else {
        setError("API 키 저장에 실패했습니다. 다시 시도해 주세요.");
      }
    } finally {
      setIsLoading(false);
    }
  };

  const handleSkip = () => {
    // 건너뛰기 시 온보딩으로 이동
    router.push("/onboarding");
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
            실시간 주식 데이터를 받기 위해 필요한 API 키들을 입력해주세요.
          </p>
        </div>

        {/* API Keys Form */}
        <div style={{ marginBottom: 32 }}>
          {/* 한국투자증권 API */}
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 12 }}>
              한국투자증권 API <span style={{ color: "#ef4444", fontSize: 12 }}>(필수)</span>
            </h3>
            <p style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", marginBottom: 12 }}>
              한국 주식 시장의 실시간 데이터를 받기 위해 필요합니다.
            </p>
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

          {/* 글로벌 주식 데이터 API (선택사항) */}
          <div style={{ marginBottom: 24 }}>
            <h3 style={{ fontSize: 16, fontWeight: 600, color: "#fff", marginBottom: 12 }}>
              글로벌 주식 데이터 API <span style={{ color: "#6b7280", fontSize: 12 }}>(선택사항)</span>
            </h3>
            <p style={{ fontSize: 12, color: "rgba(255,255,255,0.5)", marginBottom: 12 }}>
              미국 등 글로벌 주식 시장 데이터를 받기 위해 필요합니다. 나중에 설정에서 추가할 수 있습니다.
            </p>
            
            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr 1fr", gap: 12 }}>
              <div>
                <label style={{ color: "rgba(255,255,255,0.8)", fontSize: 14, marginBottom: 6, display: "block" }}>Alpha Vantage</label>
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
                <p style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginTop: 4 }}>기술적 지표 분석용</p>
              </div>
              
              <div>
                <label style={{ color: "rgba(255,255,255,0.8)", fontSize: 14, marginBottom: 6, display: "block" }}>Polygon</label>
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
                <p style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginTop: 4 }}>실시간 글로벌 데이터</p>
              </div>
              
              <div>
                <label style={{ color: "rgba(255,255,255,0.8)", fontSize: 14, marginBottom: 6, display: "block" }}>Finnhub</label>
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
                <p style={{ fontSize: 10, color: "rgba(255,255,255,0.4)", marginTop: 4 }}>뉴스 및 재무 데이터</p>
              </div>
            </div>
          </div>
        </div>

        {/* API 키 발급 안내 */}
        <div style={{ 
          background: "rgba(59, 130, 246, 0.1)", 
          border: "1px solid rgba(59, 130, 246, 0.3)", 
          borderRadius: 8, 
          padding: 16,
          marginBottom: 24
        }}>
          <div style={{ display: "flex", alignItems: "flex-start", gap: 12 }}>
            <AlertCircle style={{ width: 20, height: 20, color: "#3b82f6", marginTop: 2, flexShrink: 0 }} />
            <div style={{ fontSize: 12, color: "rgba(255,255,255,0.8)" }}>
              <p style={{ fontWeight: 600, marginBottom: 8, color: "#3b82f6" }}>API 키 발급 방법:</p>
              <ul style={{ listStyle: "none", padding: 0, margin: 0, lineHeight: 1.6 }}>
                <li>• <strong>한국투자증권</strong>: <a href="https://securities.koreainvestment.com/main/index.jsp" target="_blank" rel="noopener noreferrer" style={{ color: "#3b82f6", textDecoration: "underline" }}>Open API 신청</a></li>
                <li>• <strong>Alpha Vantage</strong>: <a href="https://www.alphavantage.co/support/#api-key" target="_blank" rel="noopener noreferrer" style={{ color: "#3b82f6", textDecoration: "underline" }}>무료 API 키 발급</a></li>
                <li>• <strong>Polygon</strong>: <a href="https://polygon.io/" target="_blank" rel="noopener noreferrer" style={{ color: "#3b82f6", textDecoration: "underline" }}>API 키 신청</a></li>
                <li>• <strong>Finnhub</strong>: <a href="https://finnhub.io/" target="_blank" rel="noopener noreferrer" style={{ color: "#3b82f6", textDecoration: "underline" }}>API 키 신청</a></li>
              </ul>
            </div>
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