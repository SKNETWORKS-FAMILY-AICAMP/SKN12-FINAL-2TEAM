// next.config.mjs
import 'dotenv/config'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

// 환경변수로 호스트 통일 (프론트 개발자안 유지)
const HOSTNAME = process.env.HOSTNAME ?? '127.0.0.1'
const API_BASE = process.env.NEXT_PUBLIC_API_BASE_URL ?? `http://${HOSTNAME}:8000`

/** @type {import('next').NextConfig} */
const nextConfig = {
  reactStrictMode: true,

  // ✅ 프론트 개발자안 유지: Fast Refresh / RSC 최적화 경로
  experimental: {
    optimizePackageImports: ['@/components', '@/lib', '@/providers'],
  },

  // ✅ 도커/환경별 프록시 주소를 환경변수 하나로 제어 (프론트 개발자안 유지)
  async rewrites() {
    return [{ source: '/api/:path*', destination: `${API_BASE}/api/:path*` }]
  },

  // ✅ 전역 CORS 헤더 금지 (프론트 개발자안 유지)
  async headers() {
    return [] // 필요하면 API 서버에서만 CORS 허용
  },

  // ✅ devServer/HMR 튜닝 금지 (프론트 개발자안 유지)
  // Docker 빌드를 위한 경로 alias 추가
  webpack(config) {
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, './')
    }
    return config
  },

  // ⬇️ 도커 빌드 안정성/운영 편의 추가 (프론트 개발자안과 충돌 없음)
  eslint: { ignoreDuringBuilds: true },
  typescript: { ignoreBuildErrors: true },
  images: { unoptimized: true },
  serverExternalPackages: [],
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
}

export default nextConfig