"use client"

import dynamic from "next/dynamic"
import type { ReactNode } from "react";

// AuthProvider가 받을 children prop의 타입을 명시적으로 정의합니다.
interface AuthProviderProps {
  children: ReactNode;
}

export const DynamicAuthProvider = dynamic<AuthProviderProps>(
  () => import("@/providers/auth-provider").then(mod => mod.AuthProvider),
  {
    ssr: false,
    loading: () => <div className="h-screen w-full flex justify-center items-center"><p>Loading authentication...</p></div>,
  },
) 