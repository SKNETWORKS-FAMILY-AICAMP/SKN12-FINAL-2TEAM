import { useState, useEffect } from "react";
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
  console.log("🔍 [useKoreaInvestApiStatus] 훅 호출됨", {
    accessToken: accessToken ? `${accessToken.substring(0, 10)}...` : null,
    currentStatus: status
  });

  useEffect(() => {
    console.log("🚀 [useKoreaInvestApiStatus] useEffect 실행됨", {
      accessToken: accessToken ? `${accessToken.substring(0, 10)}...` : null,
      timestamp: new Date().toISOString()
    });

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
        
        // OAuth 인증 상태 직접 확인
        const response = await fetch(`${process.env.NEXT_PUBLIC_API_URL}/api/dashboard/oauth`, {
          method: "POST",
          credentials: "omit",
          headers: {
            "Content-Type": "application/json",
            "Authorization": `Bearer ${accessToken}`,
          },
          body: JSON.stringify({
            accessToken: accessToken, // accessToken을 body에 포함
            sequence: Date.now(), // 현재 시간을 sequence로 사용
          }),
        });
        
        console.log("📥 [useKoreaInvestApiStatus] OAuth 응답 받음", {
          status: response.status,
          ok: response.ok,
          bodyUsed: response.bodyUsed,
          url: response.url
        });
        
        if (!response.ok) {
          console.error("❌ [useKoreaInvestApiStatus] OAuth 응답이 성공이 아님", response.status);
          throw new Error("OAuth 인증 확인 실패");
        }
        
        // HTTP 상태 코드가 200이어도 실제 응답 데이터를 확인해야 함
        try {
          console.log("📖 [useKoreaInvestApiStatus] Response body 읽기 시도");
          const data = await response.json();
          console.log("📊 [useKoreaInvestApiStatus] OAuth 응답 데이터:", data);
          
          // 실제 응답 데이터에서 성공 여부 확인
          if (data.errorCode === 0 && data.result === 'success') {
            console.log("🎉 [useKoreaInvestApiStatus] OAuth 성공 확인 (응답 데이터), isConfigured: true로 설정");
            setStatus({
              isConfigured: true,
              isLoading: false,
              error: null,
            });
            console.log("✅ [useKoreaInvestApiStatus] 상태 업데이트 완료: isConfigured = true");
            return;
          } else {
            console.log("⚠️ [useKoreaInvestApiStatus] OAuth 실패, API 키 상태 확인으로 폴백");
            // OAuth 실패 시 API 키 상태 확인 (기존 방식)
            await checkApiKeysStatus();
          }
        } catch (jsonError) {
          console.log("📝 [useKoreaInvestApiStatus] Response body 읽기 실패, API 키 상태 확인으로 폴백", jsonError);
          // JSON 읽기 실패 시 API 키 상태 확인
          await checkApiKeysStatus();
        }
        
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
      
      try {
        // profileService를 사용하여 API 키 조회
        const apiKeysResponse = await profileService.getApiKeys() as any;
        console.log("📥 [useKoreaInvestApiStatus] API 키 응답 받음:", apiKeysResponse);
        
        // errorCode가 9007이어도 api_keys 필드를 확인 (9007은 "API 키 없음"을 의미할 수 있음)
        if (apiKeysResponse.errorCode !== 0 && apiKeysResponse.errorCode !== 9007) {
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
    };

    checkOAuthStatus();
  }, [accessToken]);

  // 디버깅: 상태가 변경될 때마다 로그 출력
  console.log("📊 [useKoreaInvestApiStatus] 현재 상태:", status);

  return status;
} 