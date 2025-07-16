"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";

const steps = [
  {
    question: "투자 경험이 어느 정도인가요?",
    options: [
      { value: "BEGINNER", label: "초보자", desc: "투자를 처음 시작합니다." },
      { value: "INTERMEDIATE", label: "중급자", desc: "몇 년간 투자 경험이 있습니다." },
      { value: "EXPERT", label: "고급자", desc: "전문적인 투자 지식을 보유하고 있습니다." },
    ],
    key: "knowledge"
  },
  {
    question: "투자 스타일을 선택해 주세요.",
    options: [
      { value: "AGGRESSIVE", label: "공격적", desc: "높은 수익을 추구하며 위험을 감수합니다." },
      { value: "MODERATE", label: "중립적", desc: "수익과 위험의 균형을 추구합니다." },
      { value: "CONSERVATIVE", label: "보수적", desc: "안정성과 자산 보존을 중시합니다." },
    ],
    key: "style"
  },
  {
    question: "투자 목표를 선택해 주세요.",
    options: [
      { value: "GROWTH", label: "성장", desc: "자산의 장기적 성장을 목표로 합니다." },
      { value: "INCOME", label: "수익", desc: "지속적인 현금 흐름을 원합니다." },
      { value: "PRESERVATION", label: "자산보존", desc: "자산의 보존과 안전을 중시합니다." },
    ],
    key: "goal"
  },
  {
    question: "주식 투자 경험 기간을 선택해 주세요.",
    options: [
      { value: "NONE", label: "없음", desc: "투자 경험이 없습니다." },
      { value: "1YEAR", label: "1년 미만", desc: "1년 미만의 경험이 있습니다." },
      { value: "1-3YEAR", label: "1~3년", desc: "1~3년의 경험이 있습니다." },
      { value: "3YEAR", label: "3년 이상", desc: "3년 이상의 경험이 있습니다." },
    ],
    key: "experience"
  },
  {
    question: "이름을 선택해 주세요.",
    options: [
      { value: "홍길동", label: "홍길동", desc: "예시 이름 1" },
      { value: "김철수", label: "김철수", desc: "예시 이름 2" },
      { value: "이영희", label: "이영희", desc: "예시 이름 3" },
      { value: "기타", label: "기타", desc: "기타 이름" },
    ],
    key: "name"
  },
  {
    question: "나이를 선택해 주세요.",
    options: [
      { value: "10대", label: "10대", desc: "10~19세" },
      { value: "20대", label: "20대", desc: "20~29세" },
      { value: "30대", label: "30대", desc: "30~39세" },
      { value: "40대", label: "40대", desc: "40~49세" },
      { value: "50대 이상", label: "50대 이상", desc: "50세 이상" },
    ],
    key: "age"
  },
  {
    question: "성별을 선택해 주세요.",
    options: [
      { value: "M", label: "남성", desc: "" },
      { value: "F", label: "여성", desc: "" },
      { value: "OTHER", label: "기타", desc: "" },
    ],
    key: "gender"
  },
];

export default function OnboardingPage() {
  const router = useRouter();
  const [step, setStep] = useState(0);
  const [answers, setAnswers] = useState<Record<string, string>>({
    knowledge: "",
    style: "",
    goal: "",
    experience: "",
    name: "",
    age: "",
    gender: "",
  });
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState("");

  const handleOption = (key: string, value: string) => {
    setAnswers({ ...answers, [key]: value });
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
      // TODO: 실제 API 연동
      setTimeout(() => {
        router.push("/dashboard");
      }, 800);
    } catch (err) {
      setError("제출에 실패했습니다. 다시 시도해 주세요.");
    } finally {
      setIsLoading(false);
    }
  };

  // 진행률 계산
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
          maxWidth: 480,
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
          {/* 질문 */}
          <h2 style={{ fontSize: 22, fontWeight: 700, color: "#fff", marginBottom: 24, textAlign: "center" }}>{steps[step].question}</h2>
          {/* 객관식 선택지 */}
          <div style={{ marginBottom: 32 }}>
            {steps[step].options.map((opt: any) => (
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
          </div>
          {error && <div style={{ color: "#f87171", fontSize: 14, marginBottom: 8 }}>{error}</div>}
          {/* 버튼 */}
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
                disabled={!answers[steps[step].key]}
                style={{
                  padding: "14px 36px",
                  borderRadius: 8,
                  fontWeight: 600,
                  fontSize: 15,
                  background: !answers[steps[step].key]
                    ? "rgba(255,255,255,0.05)"
                    : "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                  color: !answers[steps[step].key] ? "#888" : "#fff",
                  border: "none",
                  cursor: !answers[steps[step].key] ? "not-allowed" : "pointer",
                  boxShadow: !answers[steps[step].key] ? "none" : "0 2px 12px #667eea33",
                  transition: "all 0.2s",
                }}
              >
                다음
              </button>
            ) : (
              <button
                type="submit"
                disabled={isLoading || !answers.name || !answers.age || !answers.gender}
                style={{
                  padding: "14px 36px",
                  borderRadius: 8,
                  fontWeight: 600,
                  fontSize: 15,
                  background: isLoading || !answers.name || !answers.age || !answers.gender
                    ? "rgba(255,255,255,0.05)"
                    : "linear-gradient(90deg, #667eea 0%, #764ba2 100%)",
                  color: isLoading || !answers.name || !answers.age || !answers.gender ? "#888" : "#fff",
                  border: "none",
                  cursor: isLoading || !answers.name || !answers.age || !answers.gender ? "not-allowed" : "pointer",
                  boxShadow: isLoading || !answers.name || !answers.age || !answers.gender ? "none" : "0 2px 12px #667eea33",
                  transition: "all 0.2s",
                }}
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