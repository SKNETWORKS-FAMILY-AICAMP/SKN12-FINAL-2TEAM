/**
 * 공통 에러 처리 유틸리티
 * 모든 기능에서 에러 코드 10000(세션 만료) 시 자동 로그인 페이지 리다이렉트
 */

export interface ApiError {
  response?: {
    data?: {
      errorCode?: number
      message?: string
    }
    status?: number
  }
  message?: string
}

export interface ErrorHandlerOptions {
  redirectToLogin?: boolean
  showAlert?: boolean
  clearSession?: boolean
}

/**
 * 에러 코드 10000(세션 만료) 처리
 * @param error API 에러 객체
 * @param options 에러 처리 옵션
 * @returns 에러 코드 10000인지 여부
 */
export function handleSessionExpired(
  error: ApiError, 
  options: ErrorHandlerOptions = {}
): boolean {
  const {
    redirectToLogin = true,
    showAlert = true,
    clearSession = true
  } = options

  // 에러 코드 10000 확인
  if (error?.response?.data?.errorCode === 10000) {
    console.log("[ERROR_HANDLER] 에러 코드 10000 감지: 세션 만료")
    
    // 현재 페이지가 로그인 페이지인지 확인
    if (typeof window !== "undefined") {
      const currentPath = window.location.pathname
      if (currentPath.startsWith("/auth/")) {
        console.log("[ERROR_HANDLER] 이미 로그인 페이지에 있음, 리다이렉트 중단")
        return true
      }
    }
    
    // 세션 정보 정리
    if (clearSession) {
      if (typeof window !== "undefined") {
        localStorage.removeItem("accessToken")
        localStorage.removeItem("auth-session")
        localStorage.removeItem("refreshToken")
        localStorage.removeItem("userId")
        console.log("[ERROR_HANDLER] 세션 정보 정리 완료")
      }
    }
    
    // 알림 표시
    if (showAlert) {
      if (typeof window !== "undefined") {
        alert("세션이 만료되었습니다. 다시 로그인해 주세요.")
      }
    }
    
    // 로그인 페이지로 리다이렉트
    if (redirectToLogin) {
      if (typeof window !== "undefined") {
        console.log("[ERROR_HANDLER] 로그인 페이지로 리다이렉트")
        window.location.href = "/auth/login"
      }
    }
    
    return true
  }
  
  return false
}

/**
 * 에러 코드별 사용자 친화적 메시지 반환
 * @param errorCode 에러 코드
 * @returns 사용자 친화적 메시지
 */
export function getErrorMessage(errorCode: number): string {
  switch (errorCode) {
    // 인증 관련
    case 10000:
      return "세션이 만료되었습니다. 다시 로그인해 주세요."
    
    // 포트폴리오 관련
    case 2000:
      return "잔액이 부족합니다."
    case 2001:
      return "잘못된 종목 코드입니다."
    case 2002:
      return "시장이 마감되었습니다."
    case 2003:
      return "주문 실행에 실패했습니다."
    case 2004:
      return "포지션을 찾을 수 없습니다."
    case 2005:
      return "잘못된 수량입니다."
    
    // 자동매매 관련
    case 4000:
      return "전략을 찾을 수 없습니다."
    case 4001:
      return "이미 활성화된 전략입니다."
    case 4002:
      return "백테스트 실행에 실패했습니다."
    case 4003:
      return "잘못된 매개변수입니다."
    case 4004:
      return "전략 실행에 실패했습니다."
    
    // 알림 관련
    case 6000:
      return "알림 서비스를 사용할 수 없습니다."
    case 6001:
      return "알림 전송에 실패했습니다."
    case 6002:
      return "알림 설정을 찾을 수 없습니다."
    case 6003:
      return "알림 구독에 실패했습니다."
    
    // 대시보드 관련
    case 7000:
      return "대시보드 데이터를 불러올 수 없습니다."
    case 7001:
      return "포트폴리오 정보를 가져올 수 없습니다."
    case 7002:
      return "시장 데이터를 가져올 수 없습니다."
    case 7003:
      return "거래 내역을 가져올 수 없습니다."
    case 7004:
      return "알림 데이터를 가져올 수 없습니다."
    
    default:
      return "알 수 없는 오류가 발생했습니다."
  }
}

/**
 * 통합 에러 처리 함수
 * @param error API 에러 객체
 * @param options 에러 처리 옵션
 * @returns 처리된 에러 정보
 */
export function handleApiError(
  error: ApiError,
  options: ErrorHandlerOptions = {}
): {
  isSessionExpired: boolean
  errorCode: number | null
  message: string
  shouldRedirect: boolean
} {
  const errorCode = error?.response?.data?.errorCode
  const isSessionExpired = handleSessionExpired(error, options)
  
  return {
    isSessionExpired,
    errorCode: errorCode || null,
    message: errorCode ? getErrorMessage(errorCode) : (error.message || "알 수 없는 오류가 발생했습니다."),
    shouldRedirect: isSessionExpired && options.redirectToLogin !== false
  }
} 