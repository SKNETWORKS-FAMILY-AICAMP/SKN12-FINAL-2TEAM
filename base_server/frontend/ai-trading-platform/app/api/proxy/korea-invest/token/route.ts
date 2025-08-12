import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { url, body, mode } = await request.json();
    
    console.log('한국투자증권 OAuth 토큰 요청:', { url, mode });
    
    // 한국투자증권 API 직접 호출
    const response = await fetch(url, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json; charset=UTF-8',
      },
      body: JSON.stringify(body),
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('한국투자증권 API 오류:', response.status, errorText);
      return NextResponse.json(
        { error: '한국투자증권 API 호출 실패', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('OAuth 토큰 발급 성공');
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('프록시 API 오류:', error);
    return NextResponse.json(
      { error: '프록시 서버 오류', details: error instanceof Error ? error.message : '알 수 없는 오류' },
      { status: 500 }
    );
  }
} 