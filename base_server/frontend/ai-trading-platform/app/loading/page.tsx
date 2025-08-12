"use client";

import { useEffect } from "react";
import { useRouter, useSearchParams } from "next/navigation";
import { LoadingSpinner } from "@/components/ui/loading-spinner";

export default function InterstitialLoadingPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const to = searchParams.get("to") || "/";
  const label = searchParams.get("label") || "다음 페이지로 이동 중...";

  useEffect(() => {
    // 짧은 인터스티셜 로딩 후 대상 경로로 교체 이동
    const timer = setTimeout(() => {
      router.replace(to);
    }, 700);
    return () => clearTimeout(timer);
  }, [router, to]);

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white flex items-center justify-center">
      <div className="text-center">
        <LoadingSpinner size="lg" className="text-blue-500" />
        <p className="mt-4 text-gray-300">{label}</p>
      </div>
    </div>
  );
}


