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
    ssr: true,
    loading: () => (
      <div className="h-screen w-full flex justify-center items-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary mx-auto mb-4"></div>
          <p className="text-foreground">Loading authentication...</p>
        </div>
      </div>
    ),
  },
) 