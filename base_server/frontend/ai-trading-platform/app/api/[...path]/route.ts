import { NextRequest, NextResponse } from 'next/server';

const API_BASE = process.env.NEXT_PUBLIC_API_URL ? `${process.env.NEXT_PUBLIC_API_URL}/api` : 'https://bullant-kr.com/api';
const TIMEOUT = 600_000; // 10분(ms)

export async function GET(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(req, params.path);
}
export async function POST(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(req, params.path);
}
export async function PUT(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(req, params.path);
}
export async function DELETE(req: NextRequest, { params }: { params: { path: string[] } }) {
  return proxyRequest(req, params.path);
}

async function proxyRequest(req: NextRequest, pathArr: string[]) {
  const url = `${API_BASE}/${pathArr.join('/')}${req.nextUrl.search}`;
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), TIMEOUT);

  try {
    const headers = Object.fromEntries(req.headers.entries());
    const fetchOptions: RequestInit = {
      method: req.method,
      headers,
      body: ['GET', 'HEAD'].includes(req.method) ? undefined : await req.text(),
      signal: controller.signal,
    };
    const response = await fetch(url, fetchOptions);

    const resHeaders = new Headers(response.headers);
    // CORS, 쿠키 등 필요시 헤더 조정
    return new NextResponse(response.body, {
      status: response.status,
      headers: resHeaders,
    });
  } catch (err) {
    return NextResponse.json({ error: 'Proxy request failed', detail: String(err) }, { status: 500 });
  } finally {
    clearTimeout(timeout);
  }
}
