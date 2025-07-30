"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import axios from "axios";

export default function SecuritiesLoginPage() {
  const [appkey, setAppkey] = useState("");
  const [appsecret, setAppsecret] = useState("");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const router = useRouter();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setIsLoading(true);

    try {
      const apiBase = process.env.NEXT_PUBLIC_API_URL;
      if (!apiBase) throw new Error("NEXT_PUBLIC_API_URL 환경변수가 필요합니다");
      const res = await axios.post(`${apiBase}/api/securities/login`, {
        appkey,
        appsecret,
        mode: "prod",
      });
      if (res.data.result === "success") {
        // 성공 시 원하는 페이지로 이동
        router.push("/dashboard");
      } else {
        setError(res.data.error || "인증 실패");
      }
    } catch (err: any) {
      setError(err.message || "네트워크 오류");
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-md mx-auto mt-16 p-8 bg-white rounded shadow">
      <h2 className="text-2xl font-bold mb-6">증권사 API 키 등록</h2>
      <form onSubmit={handleSubmit}>
        <div className="mb-4">
          <label className="block mb-1 font-semibold">App Key</label>
          <input
            type="text"
            value={appkey}
            onChange={e => setAppkey(e.target.value)}
            className="w-full border rounded px-3 py-2"
            required
          />
        </div>
        <div className="mb-4">
          <label className="block mb-1 font-semibold">App Secret</label>
          <input
            type="password"
            value={appsecret}
            onChange={e => setAppsecret(e.target.value)}
            className="w-full border rounded px-3 py-2"
            required
          />
        </div>
        {error && <div className="text-red-500 mb-2">{error}</div>}
        <button
          type="submit"
          className="w-full bg-blue-600 text-white py-2 rounded font-bold"
          disabled={isLoading}
        >
          {isLoading ? "인증 중..." : "API 키 인증"}
        </button>
      </form>
    </div>
  );
}
