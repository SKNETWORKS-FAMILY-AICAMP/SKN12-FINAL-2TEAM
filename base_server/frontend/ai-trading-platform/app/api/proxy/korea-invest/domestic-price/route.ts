import { NextRequest, NextResponse } from 'next/server';

export async function POST(request: NextRequest) {
  try {
    const { url, headers, params } = await request.json();
    
    console.log('국내 주식 가격 조회:', { symbol: params?.FID_INPUT_ISCD });
    
    // URL 파라미터 구성
    const urlParams = new URLSearchParams(params);
    const fullUrl = `${url}?${urlParams.toString()}`;
    
    // 한국투자증권 API 직접 호출
    const response = await fetch(fullUrl, {
      method: 'GET',
      headers: headers,
    });

    if (!response.ok) {
      const errorText = await response.text();
      console.error('국내 주식 API 오류:', response.status, errorText);
      return NextResponse.json(
        { error: '국내 주식 API 호출 실패', details: errorText },
        { status: response.status }
      );
    }

    const data = await response.json();
    console.log('국내 주식 가격 조회 성공');
    
    return NextResponse.json(data);
  } catch (error) {
    console.error('프록시 API 오류:', error);
    return NextResponse.json(
      { error: '프록시 서버 오류', details: error instanceof Error ? error.message : '알 수 없는 오류' },
      { status: 500 }
    );
  }
} 