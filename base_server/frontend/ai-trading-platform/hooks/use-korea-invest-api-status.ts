import { useState, useEffect, useRef } from "react";
import { profileService } from "@/lib/api/profile";

interface KoreaInvestApiStatus {
  isConfigured: boolean;
  isLoading: boolean;
  error: string | null
}

export function useKoreaInvestApiStatus(): KoreaInvestApiStatus {
  const [status, setStatus] = useState<KoreaInvestApiStatus>({
    isConfigured: false,
    isLoading: true,
    error: null,
  });
  
  // localStorage에서 직접 accessToken 가져오기 (시그널 페이지와 동일한 방식)
  const getAccessToken = (): string | null => {
    if (typeof window !== "undefined") {
      return localStorage.getItem("accessToken");
    }
    return null;
  };

  // 디버깅: 훅이 호출될 때마다 로그 출력
  const accessToken = getAccessToken();
  const didRunRef = useRef(false);
  console.log("🔍 [useKoreaInvestApiStatus] 훅 호출됨", {
    accessToken: accessToken ? `${accessToken.substring(0, 10)}...` : null,
    currentStatus: status
  });

  useEffect(() => {
    console.log("🚀 [useKoreaInvestApiStatus] useEffect 실행됨", {
      accessToken: accessToken ? `${accessToken.substring(0, 10)}...` : null,
      timestamp: new Date().toISOString()
    });

    // 전역 이벤트 리스너 추가 (API 키 필요 이벤트 감지)
    const handleApiKeyRequired = (event: CustomEvent) => {
      console.log("🚨 [useKoreaInvestApiStatus] API 키 필요 이벤트 감지:", event.detail);
      setStatus({
        isConfigured: false,
        isLoading: false,
        error: event.detail.message || "API 키가 설정되지 않았습니다."
      });
    };

    // 이벤트 리스너 등록
    window.addEventListener("api_key_required", handleApiKeyRequired as EventListener);

    const checkOAuthStatus = async () => {
      console.log("📡 [useKoreaInvestApiStatus] OAuth 상태 확인 시작");
      
      try {
        console.log("🔄 [useKoreaInvestApiStatus] 상태를 로딩으로 설정");
        setStatus(prev => ({ ...prev, isLoading: true, error: null }));
        
        // accessToken이 없으면 로딩 상태 유지
        if (!accessToken) {
          console.log("⚠️ [useKoreaInvestApiStatus] accessToken이 없음, 로딩 상태 유지");
          setStatus(prev => ({ ...prev, isLoading: true }));
          return;
        }
        
        console.log("✅ [useKoreaInvestApiStatus] accessToken 확인됨, OAuth 호출 시작");
        // Next 라우트(직렬화/inFlight) 사용 → 백엔드 중복 호출 방지
        try {
          const res = await fetch('/api/dashboard/oauth/authenticate', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ accessToken })
          });
          console.log("📥 [useKoreaInvestApiStatus] authenticate 응답", { status: res.status, ok: res.ok });
          if (res.ok) {
            setStatus({ isConfigured: true, isLoading: false, error: null });
            return;
          }
        } catch (e) {
          console.log("⚠️ [useKoreaInvestApiStatus] authenticate 실패 → API 키 상태 확인 폴백", e);
        }
        // authenticate 실패 시 기존 API 키 상태 확인
        await checkApiKeysStatus();
        
      } catch (error) {
        console.error("💥 [useKoreaInvestApiStatus] 한국투자증권 API 상태 확인 실패:", error);
        setStatus({
          isConfigured: false,
          isLoading: false,
          error: error instanceof Error ? error.message : "알 수 없는 오류",
        });
        console.log("❌ [useKoreaInvestApiStatus] 에러 상태로 설정 완료");
      }
    };

    // API 키 상태 확인 함수 (별도 분리)
    const checkApiKeysStatus = async () => {
      console.log("🔑 [useKoreaInvestApiStatus] API 키 상태 확인 시작");
      
      // 간단하게 API 키가 설정되지 않은 것으로 처리
      console.log("❌ [useKoreaInvestApiStatus] API 키 미설정으로 처리");
      setStatus({ 
        isConfigured: false, 
        isLoading: false, 
        error: "한국투자증권 API 키가 설정되지 않았습니다." 
      });
      
      // 기존 복잡한 로직은 주석 처리
      /*
      try {
        // profileService를 사용하여 API 키 조회
        const apiKeysResponse = await profileService.getApiKeys() as any;
        console.log("📥 [useKoreaInvestApiStatus] API 키 응답 받음:", apiKeysResponse);
        
        // errorCode가 9007이면 API 키가 설정되지 않은 것
        if (apiKeysResponse.errorCode === 9007) {
          console.log("❌ [useKoreaInvestApiStatus] API 키 조회 실패 (errorCode: 9007) - API 키 미설정");
          setStatus({ 
            isConfigured: false, 
            isLoading: false, 
            error: "한국투자증권 API 키가 설정되지 않았습니다." 
          });
          return;
        }
        
        // errorCode가 0이 아니면 에러
        if (apiKeysResponse.errorCode !== 0) {
          throw new Error("API 키 조회 실패");
        }
        
        const apiKeysData = apiKeysResponse.data || apiKeysResponse;
        console.log("📊 [useKoreaInvestApiStatus] API 키 데이터:", apiKeysData);
        
        // api_keys 객체의 실제 내용 확인
        if (apiKeysData.api_keys) {
          console.log("🔍 [useKoreaInvestApiStatus] api_keys 객체 내용:", apiKeysData.api_keys);
          console.log("🔍 [useKoreaInvestApiStatus] korea_investment_app_key:", apiKeysData.api_keys.korea_investment_app_key);
          console.log("🔍 [useKoreaInvestApiStatus] korea_investment_app_secret_masked:", apiKeysData.api_keys.korea_investment_app_secret_masked);
        }
        
        // 한국투자증권 API 키가 설정되어 있는지 확인
        const hasKoreaInvestApi = apiKeysData.api_keys && 
                                 apiKeysData.api_keys.korea_investment_app_key && 
                                 apiKeysData.api_keys.korea_investment_app_secret_masked && 
                                 apiKeysData.api_keys.korea_investment_app_key.trim() !== '' && 
                                 apiKeysData.api_keys.korea_investment_app_secret_masked.trim() !== '';
        
        console.log("🔍 [useKoreaInvestApiStatus] API 키 설정 여부:", hasKoreaInvestApi);
        
        setStatus({
          isConfigured: Boolean(hasKoreaInvestApi), // 명시적으로 boolean으로 변환
          isLoading: false,
          error: null,
        });
        
        console.log("✅ [useKoreaInvestApiStatus] API 키 상태 업데이트 완료:", {
          isConfigured: Boolean(hasKoreaInvestApi),
          isLoading: false
        });
        
      } catch (error) {
        console.error("💥 [useKoreaInvestApiStatus] API 키 상태 확인 실패:", error);
        setStatus({
          isConfigured: false,
          isLoading: false,
          error: "API 키 상태 확인 실패",
        });
        console.log("❌ [useKoreaInvestApiStatus] API 키 에러 상태로 설정 완료");
      }
      */
    };

    if (didRunRef.current) return; // StrictMode 중복 방지
    didRunRef.current = true;
    checkOAuthStatus();

    // cleanup 함수
    return () => {
      window.removeEventListener("api_key_required", handleApiKeyRequired as EventListener);
    };
  }, [accessToken]);

  // 디버깅: 상태가 변경될 때마다 로그 출력
  console.log("📊 [useKoreaInvestApiStatus] 현재 상태:", status);

  return status;
} 