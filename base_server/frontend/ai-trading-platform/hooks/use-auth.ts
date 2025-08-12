"use client";

import { useAuth as useAuthContext } from "@/providers/auth-provider";

// provider가 반환하는 타입에 accessTokenReady를 덧붙여서 리턴
type AuthCtx = ReturnType<typeof useAuthContext>;
type WithReady = AuthCtx & { accessTokenReady: boolean };

export function useAuth(): WithReady {
  const ctx = useAuthContext();

  // 👉 provider에서 어떤 이름을 쓰는지에 맞춰 조정
  const accessToken =
    // 1) 직접 토큰
    (ctx as any).accessToken ??
    // 2) 세션 객체 내부
    (ctx as any).session?.accessToken ??
    // 3) 로컬 상태 등
    (ctx as any).token;

  const accessTokenReady = Boolean(accessToken);

  return { ...ctx, accessTokenReady };
}

