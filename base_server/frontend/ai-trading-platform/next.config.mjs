import 'dotenv/config';

/** @type {import('next'). NextConfig} */
const nextConfig = {
  eslint: {
    ignoreDuringBuilds: true,
  },
  typescript: {
    ignoreBuildErrors: true,
  },
  images: {
    unoptimized: true,
  },
  // RSC 최적화 설정 (Next.js 15 호환)
  experimental: {
    optimizePackageImports: [],
  },
  // 서버 외부 패키지 설정
  serverExternalPackages: [],
  // 개발 서버 설정
  devIndicators: {
    position: 'bottom-right',
  },
  // 웹팩 설정
  webpack: (config, { dev, isServer }) => {
    if (dev && !isServer) {
      // 개발 환경에서 HMR 최적화 (Next.js 기본 설정만 사용)
      config.watchOptions = {
        poll: 1000,
        aggregateTimeout: 300,
      };
    }
    return config;
  },
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization, X-Requested-With',
          },
          {
            key: 'Access-Control-Allow-Credentials',
            value: 'true',
          },
        ],
      },
    ];
  },
  async rewrites() {
    console.log("[NEXT.JS] API 프록시 설정 로드됨");
    return [
      // 모든 API 요청을 백엔드로 프록시
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
    ];
  },
  // scroll-behavior 경고 해결
  compiler: {
    removeConsole: process.env.NODE_ENV === 'production',
  },
}

export default nextConfig
