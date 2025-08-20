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
  // experimental: {
  //   appDir: true,  // Next.js 15에서 제거됨 - App Router가 기본값
  // },
  env: {
    // 기본 환경 변수 설정 (개발용)
    NEXT_PUBLIC_API_URL: process.env.NEXT_PUBLIC_API_URL || 'https://bullant-kr.com',
    NEXT_PUBLIC_API_BASE: process.env.NEXT_PUBLIC_API_BASE || 'https://bullant-kr.com',
    NEXT_PUBLIC_WS_URL: process.env.NEXT_PUBLIC_WS_URL || 'wss://bullant-kr.com',
  },
  async rewrites() {
    return [
      {
        source: '/api/:path*',
        destination: `${process.env.NEXT_PUBLIC_API_URL || 'https://bullant-kr.com'}/api/:path*`,
      },
    ];
  },
  async headers() {
    return [
      {
        source: '/(.*)',
        headers: [
          {
            key: 'X-Frame-Options',
            value: 'DENY',
          },
          {
            key: 'X-Content-Type-Options',
            value: 'nosniff',
          },
          {
            key: 'Referrer-Policy',
            value: 'origin-when-cross-origin',
          },
        ],
      },
    ];
  },
  webpack: (config, { buildId, dev, isServer, defaultLoaders, webpack }) => {
    // 🔧 경로 별칭(@) 설정 - Docker 빌드 호환성
    config.resolve.alias = {
      ...config.resolve.alias,
      '@': path.resolve(__dirname, './'),
    };
    
    // WebSocket 지원을 위한 설정
    config.externals = config.externals || [];
    if (!isServer) {
      config.externals.push({
        'utf-8-validate': 'commonjs utf-8-validate',
        'bufferutil': 'commonjs bufferutil',
      });
    }
    return config;
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