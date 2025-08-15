// 환경변수로 호스트 통일
const HOSTNAME = process.env.HOSTNAME ?? '127.0.0.1'
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? `http://${HOSTNAME}:8000`

const nextConfig = {
  reactStrictMode: true,
  
  // Fast Refresh 최적화
  experimental: {
    optimizePackageImports: ['@/components', '@/lib', '@/providers'],
  },

  async rewrites() {
    return [
      { source: '/api/:path*', destination: `${API_BASE}/api/:path*` },
    ]
  },

  // ⛔️ 전역 CORS 헤더 금지 (특히 /_next/* 에 절대 붙이지 말 것)
  async headers() {
    return []   // 필요하면 API 서버 쪽에서만 CORS 열기
  },

  // ⛔️ devServer/HMR 플러그인/튜닝 금지: Next가 관리함
  webpack(config) {
    return config
  },
}

export default nextConfig
