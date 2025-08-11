import 'dotenv/config';

/** @type {import('next').NextConfig} */
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
      // 개발 환경에서 HMR 최적화
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
        source: '/(.*)',
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
    return [
      {
        source: '/api/:path*',
        destination: 'http://localhost:8000/api/:path*',
      },
      // notification 엔드포인트 추가
      {
        source: '/notification/:path*',
        destination: 'http://127.0.0.1:8000/notification/:path*',
      },
    ];
  },
}

export default nextConfig
