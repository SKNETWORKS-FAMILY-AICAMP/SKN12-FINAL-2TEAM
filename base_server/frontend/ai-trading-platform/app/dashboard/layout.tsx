"use client";

import type React from "react"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"
import { Header } from "@/components/layout/header"
import { AppSidebar } from "@/components/layout/AppSidebar" // 대문자 A, props 받는 버전
// import { useAuth } from "@/hooks/use-auth"
import { LoadingSpinner } from "@/components/ui/loading-spinner"

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  // const { user, isLoading } = useAuth()
  const router = useRouter()
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const [checked, setChecked] = useState(false);

  // 페이지 이동 핸들러
  const handleNavigate = (key: string) => {
    switch (key) {
      case "dashboard":
        router.push("/dashboard"); break;
      case "portfolio":
        router.push("/portfolio"); break;
      case "signals":
        router.push("/autotrade"); break;
      case "chat":
        router.push("/chat"); break;
      case "settings":
        router.push("/settings"); break;
      default:
        break;
    }
    setSidebarOpen(false);
  };

  useEffect(() => {
    const token = typeof window !== "undefined" ? localStorage.getItem("accessToken") : null;
    if (!token) {
      router.push("/auth/login");
    } else {
      setChecked(true);
    }
  }, [router]);

  if (!checked) return null;

  return (
    <>
      <Header onSidebarOpen={() => setSidebarOpen(true)} />
      <AppSidebar open={sidebarOpen} onClose={() => setSidebarOpen(false)} onNavigate={handleNavigate} />
      <main>
        {children}
      </main>
    </>
  )
}
