"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { setupProfile, SetupProfilePayload } from "@/lib/api/profile";
import { handleSessionExpired } from "@/lib/error-handler";

const steps: Array<{
  key: string;
  question: string;
  options?: { value: string; label: string; desc: string }[];
  type: "select" | "input";
}> = [
  {
    key: "investment_experience",
    question: "당신의 투자 경험은 어느 정도인가요?",
    options: [
      { value: "초급", label: "초급", desc: "투자를 처음 시작합니다." },
      { value: "중급", label: "중급", desc: "몇 년간 투자 경험이 있습니다." },
      { value: "고급", label: "고급", desc: "전문적인 투자 지식을 보유하고 있습니다." },
    ],
    type: "select",
  },
  {
    key: "risk_tolerance",
    question: "당신의 투자 성향은 무엇인가요?",
    options: [
      { value: "보수적", label: "보수적", desc: "안정성과 자산 보존을 중시합니다." },
      { value: "보통", label: "보통", desc: "수익과 위험의 균형을 추구합니다." },
      { value: "공격적", label: "공격적", desc: "높은 수익을 추구하며 위험을 감수합니다." },
    ],
    type: "select",
  },
  {
    key: "investment_goal",
    question: "당신의 투자 목표는 무엇인가요?",
    options: [
      { value: "장기투자", label: "장기투자", desc: "자산의 장기적 성장을 목표로 합니다." },
      { value: "단기수익", label: "단기수익", desc: "단기적인 수익을 추구합니다." },
      { value: "안정성", label: "안정성", desc: "자산의 보존과 안전을 중시합니다." },
    ],
    type: "select",
  },
  {
    key: "monthly_budget",
    question: "월 투자 예산을 입력해 주세요 (숫자만)",
    type: "input",
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({
    investment_experience: "",
    risk_tolerance: "",
    investment_goal: "",
    monthly_budget: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  useEffect(() => {
    // 토큰 확인만 하고 로그는 출력하지 않음
    if (typeof window !== "undefined") {
      const accessToken = localStorage.getItem("accessToken");
      if (!accessToken) {
        router.push("/auth/login");
      }
    }
  }, []);

  const handleOption = (key: string, value: string) => {
    setAnswers((prev) => ({ ...prev, [key]: value }));
  };
  const handleInput = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value.replace(/[^0-9.]/g, "");
    setAnswers((prev) => ({ ...prev, monthly_budget: value }));
  };
  const handleNext = () => {
    if (step < steps.length - 1) setStep(step + 1);
  };
  const handlePrev = () => {
    if (step > 0) setStep(step - 1);
  };
  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError("");
    try {
      const experienceMap: Record<string, "BEGINNER" | "INTERMEDIATE" | "EXPERT"> = {
        "초급": "BEGINNER",
        "중급": "INTERMEDIATE",
        "고급": "EXPERT",
      };
      const riskMap: Record<string, "CONSERVATIVE" | "MODERATE" | "AGGRESSIVE"> = {
        "보수적": "CONSERVATIVE",
        "보통": "MODERATE",
        "공격적": "AGGRESSIVE",
      };
      const goalMap: Record<string, "GROWTH" | "INCOME" | "PRESERVATION"> = {
        "장기투자": "GROWTH",
        "단기수익": "INCOME",
        "안정성": "PRESERVATION",
      };
      const payload: SetupProfilePayload = {
        investment_experience: experienceMap[answers.investment_experience],
        risk_tolerance: riskMap[answers.risk_tolerance],
        investment_goal: goalMap[answers.investment_goal],
        monthly_budget: parseFloat(answers.monthly_budget),
      };
      
      console.log("[온보딩] 프로필 설정 요청:", payload);
      
      // setupProfile 함수 직접 호출
      const res = await setupProfile(payload);
      
      console.log("[온보딩] 백엔드 응답:", res);
      
      // 응답이 문자열인 경우 JSON 파싱
      let parsedRes: any = res;
      if (typeof res === 'string') {
        try {
          parsedRes = JSON.parse(res);
        } catch (parseError) {
          console.error("[온보딩] JSON 파싱 에러:", parseError);
          setError("서버 응답을 처리할 수 없습니다.");
          return;
        }
      }
      
      // 응답 구조에 따라 profile 위치를 체크
      const profile = parsedRes?.profile || parsedRes?.data?.profile;
      const errorCode = parsedRes?.errorCode;
      const message = parsedRes?.message;
      
      console.log("[온보딩] 파싱된 응답:", { errorCode, profile, message });
      
      // 에러 코드 10000 (세션 만료) 처리
      if (errorCode === 10000) {
        console.log("[온보딩] 에러 코드 10000 감지: 세션 만료");
        setError("세션이 만료되었습니다. 로그인 페이지로 이동합니다.");
        
        // 2초 후 세션 만료 처리 및 리다이렉
        setTimeout(() => {
          handleSessionExpired({ response: { data: { errorCode: 10000 } } });
        }, 2000);
        return;
      }
      
      // 성공 조건: errorCode가 0이고 profile이 존재하거나, profile이 존재하는 경우
      if (errorCode === 0 || profile) {
        console.log("[온보딩] 프로필 설정 성공, 대시보드로 이동");
        // 부드러운 페이지 전환
        router.push("/dashboard");
      } else {
        const errorMessage = message || parsedRes?.data?.message || "프로필 설정에 실패했습니다.";
        setError(errorMessage);
      }
    } catch (err: any) {
      console.error("[온보딩] 에러 발생:", err);
      
      // catch 블록에서도 error code 10000 체크
      if (err?.response?.data?.errorCode === 10000) {
        console.log("[온보딩] catch 블록에서 에러 코드 10000 감지: 세션 만료");
        setError("세션이 만료되었습니다. 로그인 페이지로 이동합니다.");
        
        // 2초 후 세션 만료 처리 및 리다이렉트
        setTimeout(() => {
          handleSessionExpired(err);
        }, 2000);
        return;
      }
      
      const errorMessage = err?.response?.data?.message || "제출에 실패했습니다. 다시 시도해 주세요.";
      setError(errorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const progress = Math.round(((step + 1) / steps.length) * 100);

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
        {/* 진행바 */}
        <div style={{ marginBottom: 24 }}>
          <div style={{ display: "flex", justifyContent: "space-between", alignItems: "center", color: "#fff", fontSize: 14, marginBottom: 4 }}>
            <span>시작</span>
            <span>{step + 1} / {steps.length}</span>
            <span>완료</span>
          </div>
          <div style={{ width: "100%", height: 8, background: "rgba(255,255,255,0.08)", borderRadius: 8, overflow: "hidden" }}>
            <div style={{ height: "100%", background: "linear-gradient(90deg, #667eea 0%, #764ba2 100%)", width: `${progress}%` }} />
          </div>
        </div>
        <form onSubmit={handleSubmit}>
          <h2 style={{ fontSize: 22, fontWeight: 700, color: "#fff", marginBottom: 24, textAlign: "center" }}>{steps[step].question}</h2>
          <div style={{ marginBottom: 32 }}>
            {steps[step].type === "select" && steps[step].options && steps[step].options.map((opt) => (
              <button
                type="button"
                key={opt.value}
                style={{
                  width: "100%",
                  display: "flex",
                  alignItems: "center",
                  justifyContent: "space-between",
                  padding: 20,
                  marginBottom: 12,
                  borderRadius: 12,
                  border: answers[steps[step].key] === opt.value ? "2px solid #67e8f9" : "1px solid rgba(255,255,255,0.12)",
                  background: answers[steps[step].key] === opt.value
                    ? "linear-gradient(90deg, #667eea22 0%, #764ba222 100%)"
                    : "rgba(10,17,32,0.85)",
                  color: answers[steps[step].key] === opt.value ? "#67e8f9" : "#fff",
                  fontWeight: 500,
                  fontSize: 17,
                  boxShadow: answers[steps[step].key] === opt.value ? "0 2px 12px #667eea33" : "none",
                  transition: "all 0.2s",
                  textAlign: "left",
                }}
                onClick={() => handleOption(steps[step].key, opt.value)}
              >
                <div>
                  <div style={{ fontWeight: 700, fontSize: 17 }}>{opt.label}</div>
                  {opt.desc && <div style={{ fontSize: 14, opacity: 0.7 }}>{opt.desc}</div>}
                </div>
                {answers[steps[step].key] === opt.value && (
                  <span style={{ marginLeft: 16, color: "#67e8f9", fontSize: 26 }}>✔</span>
                )}
              </button>
            ))}
            {steps[step].type === "input" && (
              <input
                type="number"
                min="0"
                step="1"
                value={answers.monthly_budget}
                onChange={handleInput}
                placeholder="예: 1000000"
                style={{
                  width: "100%",
                  padding: "16px 18px",
                  borderRadius: 10,
                  background: "rgba(30,35,50,0.95)",
                  border: "1px solid rgba(255,255,255,0.12)",
                  color: "#fff",
                  fontSize: 16,
                  marginBottom: 8,
                  outline: "none",
                  boxShadow: "none",
                  transition: "border 0.2s",
                }}
                required
              />
            )}
          </div>
          {error && <div style={{ color: "#f87171", fontSize: 14, marginBottom: 8 }}>{error}</div>}
          <div style={{ display: "flex", justifyContent: "space-between", marginTop: 32 }}>
            <button
              type="button"
              onClick={handlePrev}
              disabled={step === 0}
              style={{
                padding: "14px 36px",
                borderRadius: 8,
                fontWeight: 600,
                fontSize: 15,
                background: step === 0 ? "rgba(255,255,255,0.05)" : "rgba(10,17,32,0.85)",
                color: step === 0 ? "#888" : "#fff",
                border: "1px solid rgba(255,255,255,0.12)",
                cursor: step === 0 ? "not-allowed" : "pointer",
                transition: "all 0.2s",
              }}
            >
              이전
            </button>
            {step < steps.length - 1 ? (
              <button
                type="button"
                onClick={handleNext}
                disabled={steps[step].type === "input" ? !answers.monthly_budget : !answers[steps[step].key]}
                style={{
                  padding: "14px 36px",
                  borderRadius: 8,
                  fontWeight: 600,
                  fontSize: 15,
                  background:
                    steps[step].type === "input"
                      ? (!answers.monthly_budget
                          ? "rgba(255,255,255,0.05)"
                          : "linear-gradient(90deg, #667eea 0%, #764ba2 100%)")
                      : "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                  color:
                    steps[step].type === "input"
                      ? (!answers.monthly_budget ? "#888" : "#fff")
                      : "#fff",
                  border: "none",
                  cursor:
                    steps[step].type === "input"
                      ? (!answers.monthly_budget ? "not-allowed" : "pointer")
                      : "pointer",
                  boxShadow:
                    steps[step].type === "input"
                      ? (!answers.monthly_budget ? "none" : "0 2px 12px #667eea33")
                      : "0 2px 12px #667eea33",
                  transition: "all 0.2s",
                }}
              >
                다음
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || !answers.investment_experience || !answers.risk_tolerance || !answers.investment_goal || !answers.monthly_budget}
                style={{
                  padding: "14px 36px",
                  borderRadius: 8,
                  fontWeight: 600,
                  fontSize: 15,
                  background: (
                    isLoading || !answers.investment_experience || !answers.risk_tolerance || !answers.investment_goal || !answers.monthly_budget
                  ) ? "rgba(255,255,255,0.05)" : "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                  color: (
                    isLoading || !answers.investment_experience || !answers.risk_tolerance || !answers.investment_goal || !answers.monthly_budget
                  ) ? "#888" : "#fff",
                  border: "none",
                  cursor: (
                    isLoading || !answers.investment_experience || !answers.risk_tolerance || !answers.investment_goal || !answers.monthly_budget
                  ) ? "not-allowed" : "pointer",
                  boxShadow: (
                    isLoading || !answers.investment_experience || !answers.risk_tolerance || !answers.investment_goal || !answers.monthly_budget
                  ) ? "none" : "0 2px 12px #667eea33",
                  transition: "all 0.2s",
                } as React.CSSProperties}
              >
                {isLoading ? "제출 중..." : "설문 완료"}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
} 