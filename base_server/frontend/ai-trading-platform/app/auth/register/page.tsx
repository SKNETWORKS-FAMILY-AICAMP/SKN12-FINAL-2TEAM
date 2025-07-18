"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import Link from "next/link"
import { Loader2, TrendingUp, Zap } from "lucide-react"
import axios from "axios"

// 1단계: 최소 정보 입력
function RegisterStep1({ form, setForm, onNext, error, isLoading }: any) {
  return (
    <form onSubmit={e => { e.preventDefault(); onNext(); }}>
      <div style={{ marginBottom: 24 }}>
        <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>이름</label>
        <input
          type="text"
          name="name"
          value={form.name}
          onChange={e => setForm((f: any) => ({ ...f, name: e.target.value }))}
          required
          placeholder="홍길동"
          style={inputStyle}
        />
      </div>
      <div style={{ marginBottom: 24 }}>
        <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>아이디</label>
        <input
          type="text"
          name="account_id"
          value={form.account_id}
          onChange={e => setForm((f: any) => ({ ...f, account_id: e.target.value }))}
          required
          placeholder="아이디"
          style={inputStyle}
        />
      </div>
      <div style={{ marginBottom: 24 }}>
        <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>비밀번호</label>
        <input
          type="password"
          name="password"
          value={form.password}
          onChange={e => setForm((f: any) => ({ ...f, password: e.target.value }))}
          required
          placeholder="최소 6자 이상"
          style={inputStyle}
        />
      </div>
      <div style={{ marginBottom: 24 }}>
        <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>비밀번호 확인</label>
        <input
          type="password"
          name="confirmPassword"
          value={form.confirmPassword}
          onChange={e => setForm((f: any) => ({ ...f, confirmPassword: e.target.value }))}
          required
          placeholder="비밀번호를 다시 입력하세요"
          style={inputStyle}
        />
      </div>
      {error && <div style={{ color: "#f87171", fontSize: 14, marginBottom: 12 }}>{error}</div>}
      <button
        type="submit"
        disabled={isLoading}
        style={buttonStyle(isLoading)}
      >
        {isLoading ? (
          <>
            <Loader2 style={{ marginRight: 8, width: 18, height: 18, verticalAlign: "middle", display: "inline-block" }} className="animate-spin" />
            다음 단계...
          </>
        ) : (
          "다음"
        )}
      </button>
    </form>
  )
}

// 2단계: 추가 정보 입력 및 최종 회원가입
function RegisterStep2({ form, setForm, onRegister, error, isLoading }: any) {
  // 입력값 검증 함수
  const validate = () => {
    // 출생연도: 4자리, 1900~현재년도
    const year = Number(form.birth_year);
    const yearStr = String(form.birth_year);
    const nowYear = new Date().getFullYear();
    if (!/^[0-9]{4}$/.test(yearStr) || year < 1900 || year > nowYear) {
      return `출생연도는 1900~${nowYear} 사이의 4자리 숫자여야 합니다.`;
    }
    // 월: 1~12, 두자리
    const month = Number(form.birth_month);
    if (!/^[0-9]{1,2}$/.test(String(form.birth_month)) || month < 1 || month > 12) {
      return '월은 1~12 사이의 숫자여야 합니다.';
    }
    // 일: 1~31, 두자리
    const day = Number(form.birth_day);
    if (!/^[0-9]{1,2}$/.test(String(form.birth_day)) || day < 1 || day > 31) {
      return '일은 1~31 사이의 숫자여야 합니다.';
    }
    return '';
  };

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const errMsg = validate();
    if (errMsg) {
      setForm((f: any) => ({ ...f, _error: errMsg }));
      return;
    }
    setForm((f: any) => ({ ...f, _error: undefined }));
    onRegister();
  };

  return (
    <form onSubmit={handleSubmit}>
      <div style={{ marginBottom: 24 }}>
        <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>닉네임</label>
        <input
          type="text"
          name="nickname"
          value={form.nickname}
          onChange={e => setForm((f: any) => ({ ...f, nickname: e.target.value }))}
          required
          placeholder="닉네임"
          style={inputStyle}
        />
      </div>
      <div style={{ marginBottom: 24 }}>
        <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>이메일</label>
        <input
          type="email"
          name="email"
          value={form.email}
          onChange={e => setForm((f: any) => ({ ...f, email: e.target.value }))}
          required
          placeholder="example@email.com"
          style={inputStyle}
        />
      </div>
      <div style={{ marginBottom: 24, display: "flex", gap: 8 }}>
        <div style={{ flex: 1 }}>
          <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>출생연도</label>
          <input
            type="number"
            name="birth_year"
            value={form.birth_year}
            onChange={e => setForm((f: any) => ({ ...f, birth_year: e.target.value.replace(/[^0-9]/g, '').slice(0, 4) }))}
            required
            placeholder="1985"
            min={1900}
            max={new Date().getFullYear()}
            maxLength={4}
            style={numberInputNoSpin}
            inputMode="numeric"
            pattern="[0-9]{4}"
          />
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>월</label>
          <input
            type="number"
            name="birth_month"
            value={form.birth_month}
            onChange={e => setForm((f: any) => ({ ...f, birth_month: e.target.value.replace(/[^0-9]/g, '').slice(0, 2) }))}
            required
            placeholder="8"
            min={1}
            max={12}
            maxLength={2}
            style={numberInputNoSpin}
            inputMode="numeric"
            pattern="[0-9]{1,2}"
          />
        </div>
        <div style={{ flex: 1 }}>
          <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>일</label>
          <input
            type="number"
            name="birth_day"
            value={form.birth_day}
            onChange={e => setForm((f: any) => ({ ...f, birth_day: e.target.value.replace(/[^0-9]/g, '').slice(0, 2) }))}
            required
            placeholder="25"
            min={1}
            max={31}
            maxLength={2}
            style={numberInputNoSpin}
            inputMode="numeric"
            pattern="[0-9]{1,2}"
          />
        </div>
      </div>
      <div style={{ marginBottom: 24 }}>
        <label style={{ color: "#fff", fontWeight: 500, marginBottom: 8, display: "block" }}>성별</label>
        <select
          name="gender"
          value={form.gender}
          onChange={e => setForm((f: any) => ({ ...f, gender: e.target.value }))}
          required
          style={{
            ...inputStyle,
            color: form.gender ? '#fff' : '#888',
            appearance: 'none',
            WebkitAppearance: 'none',
            MozAppearance: 'none',
            background: 'rgba(30,35,50,0.95)',
            border: '1px solid rgba(255,255,255,0.12)',
            paddingRight: 32,
            position: 'relative',
            backgroundImage: `url("data:image/svg+xml;utf8,<svg fill='white' height='16' viewBox='0 0 24 24' width='16' xmlns='http://www.w3.org/2000/svg'><path d='M7 10l5 5 5-5z'/></svg>")`,
            backgroundRepeat: 'no-repeat',
            backgroundPosition: 'right 12px center',
            backgroundSize: '18px 18px',
          }}
        >
          <option value="">성별 선택</option>
          <option value="M">남자</option>
          <option value="F">여자</option>
        </select>
      </div>
      {form._error && <div style={{ color: "#f87171", fontSize: 14, marginBottom: 12 }}>{form._error}</div>}
      {error && <div style={{ color: "#f87171", fontSize: 14, marginBottom: 12 }}>{error}</div>}
      <button
        type="submit"
        disabled={isLoading}
        style={buttonStyle(isLoading)}
      >
        {isLoading ? (
          <>
            <Loader2 style={{ marginRight: 8, width: 18, height: 18, verticalAlign: "middle", display: "inline-block" }} className="animate-spin" />
            회원가입 중...
          </>
        ) : (
          "회원가입"
        )}
      </button>
    </form>
  )
}

// 글로벌 스타일 추가 (최상단)
import './register.css';

const inputStyle = {
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
};

// 추가: input[type=number]의 spin button 제거 (Webkit)
const numberInputNoSpin = {
  ...inputStyle
};

const buttonStyle = (isLoading: boolean) => ({
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
})

// 에러 코드 → 메시지 매핑 추가
const ERROR_MESSAGES: Record<number, string> = {
  0: "성공",
  1001: "인증에 실패했습니다.",
  1002: "권한이 없습니다.",
  1003: "입력 정보를 확인해주세요.",
  1004: "요청한 정보를 찾을 수 없습니다.",
  1005: "서버 오류가 발생했습니다.",
  1007: "비밀번호가 너무 약합니다.",
  1008: "이미 등록된 이메일입니다.",
  1009: "이미 등록된 아이디입니다.",
  // 필요시 추가
};

function getErrorMessage(errorCode: number, defaultMsg?: string) {
  return ERROR_MESSAGES[errorCode] || defaultMsg || `오류가 발생했습니다. (코드: ${errorCode})`;
}

export default function RegisterPage() {
  const [form, setForm] = useState({
    name: "",
    account_id: "",
    password: "",
    confirmPassword: "",
    nickname: "",
    email: "",
    birth_year: 2000,
    birth_month: 1,
    birth_day: 1,
    gender: "M"
  })
  const [step, setStep] = useState(1)
  const [error, setError] = useState("")
  const [isLoading, setIsLoading] = useState(false)
  const router = useRouter()

  // 1단계 완료 → 2단계로 이동
  const handleNext = () => {
    setError("")
    if (form.password !== form.confirmPassword) {
      setError("비밀번호가 일치하지 않습니다.")
      return
    }
    if (form.password.length < 6) {
      setError("비밀번호는 최소 6자 이상이어야 합니다.")
      return
    }
    setStep(2)
  }

  // 2단계에서 최종 회원가입 요청
  const handleRegister = async () => {
    setError("")
    setIsLoading(true)
    try {
      const res = await axios.post("http://127.0.0.1:8000/api/account/signup", {
        sequence: Date.now(),
        platform_type: 1,
        account_id: form.account_id,
        password: form.password,
        password_confirm: form.confirmPassword,
        nickname: form.nickname || form.name,
        email: form.email,
        name: form.name,
        birth_year: Number(form.birth_year),
        birth_month: Number(form.birth_month),
        birth_day: Number(form.birth_day),
        gender: form.gender
      })
      let data = res.data;
      if (typeof data === "string") {
        try {
          data = JSON.parse(data);
        } catch (parseErr) {
          console.error("회원가입 응답 파싱 에러:", parseErr, data);
          setError("서버 응답 파싱 오류가 발생했습니다.");
          setIsLoading(false);
          return;
        }
      }
      console.log('회원가입 응답:', data);
      if (data.errorCode === 0 || data.errorCode === "0") {
        if (data.accessToken) {
          localStorage.setItem('accessToken', data.accessToken)
        }
        router.push("/auth/login")
        return; // router.push 후 return 추가
      } else {
        console.log('회원가입 실패 errorCode:', data.errorCode, 'message:', data.message);
        setError(getErrorMessage(data.errorCode, data.message))
      }
    } catch (e: any) {
      console.error("회원가입 에러:", e); // 에러 콘솔 출력 추가
      const errorCode = e?.response?.data?.errorCode;
      const message = e?.response?.data?.message;
      setError(getErrorMessage(errorCode, message || "회원가입에 실패했습니다. 다시 시도해주세요."));
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
        {/* Register Form */}
        {step === 1 ? (
          <RegisterStep1 form={form} setForm={setForm} onNext={handleNext} error={error} isLoading={isLoading} />
        ) : (
          <RegisterStep2 form={form} setForm={setForm} onRegister={handleRegister} error={error} isLoading={isLoading} />
        )}
        <div style={{ textAlign: "center", fontSize: 14, color: "#a5b4fc" }}>
          <span>이미 계정이 있으신가요? </span>
          <Link href="/auth/login" style={{ color: "#67e8f9", fontWeight: 500 }}>로그인</Link>
        </div>
      </div>
    </div>
  )
}
