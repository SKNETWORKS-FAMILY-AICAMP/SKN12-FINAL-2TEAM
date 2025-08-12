'use client';

import React, { useEffect, useRef } from 'react';
import { useIndices, IndexTick } from '@/hooks/use-indices';
import { cn } from '@/lib/utils';
import { Badge } from '@/components/ui/badge';
import { Card, CardContent } from '@/components/ui/card';

interface IndexChipProps {
  index: IndexTick;
}

const IndexChip: React.FC<IndexChipProps> = ({ index }) => {
  const isPositive = index.change_pct >= 0;  // 변동률 기준으로 변경
  const isActive = index.status === 'active';
  const isFresh = index.is_fresh;
  
  // 상태에 따른 배지 색상
  const getStatusColor = () => {
    if (!isActive) return 'bg-gray-500';
    if (!isFresh) return 'bg-yellow-500';
    return 'bg-green-500';
  };

  // 상태 텍스트
  const getStatusText = () => {
    if (!isActive) return '오류';
    if (!isFresh) return '지연';
    return '실시간';
  };

  return (
    <div className="flex items-center space-x-2 bg-background border rounded-lg px-3 py-2 min-w-[200px]">
      {/* 인덱스 이름 */}
      <div className="flex-1 min-w-0">
        <div className="font-medium text-sm truncate">{index.name}</div>
        <div className="text-xs text-muted-foreground">{index.symbol}</div>
      </div>
      
      {/* 가격 정보 */}
      <div className="text-right">
        <div className={cn(
          "font-bold text-sm",
          isPositive ? "text-red-600" : "text-blue-600"
        )}>
          {index.price > 0 ? index.price.toLocaleString() : 'N/A'}
        </div>
        <div className={cn(
          "text-xs",
          isPositive ? "text-red-600" : "text-blue-600"
        )}>
          {index.change >= 0 ? '+' : ''}{index.change.toFixed(2)} ({index.change_pct >= 0 ? '+' : ''}{index.change_pct.toFixed(2)}%)
        </div>
      </div>
      
      {/* 상태 배지 */}
      <Badge 
        variant="secondary" 
        className={cn("text-xs", getStatusColor())}
      >
        {getStatusText()}
      </Badge>
    </div>
  );
};

const IndicesTicker: React.FC = () => {
  const { 
    indices, 
    isConnected, 
    error, 
    getKoreaIndices, 
    getUSIndices, 
    getFX,
    reconnect 
  } = useIndices();
  
  const containerRef = useRef<HTMLDivElement>(null);
  const animationRef = useRef<number>();

  // 무한 스크롤 애니메이션
  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    let scrollPosition = 0;
    const scrollSpeed = 1; // 픽셀/프레임

    const animate = () => {
      if (container) {
        scrollPosition += scrollSpeed;
        
        // 컨테이너 너비만큼 스크롤되면 처음으로
        if (scrollPosition >= container.scrollWidth / 2) {
          scrollPosition = 0;
        }
        
        container.scrollLeft = scrollPosition;
      }
      animationRef.current = requestAnimationFrame(animate);
    };

    animationRef.current = requestAnimationFrame(animate);

    return () => {
      if (animationRef.current) {
        cancelAnimationFrame(animationRef.current);
      }
    };
  }, []);

  const koreaIndices = getKoreaIndices();
  const usIndices = getUSIndices();
  const fx = getFX();

  // 모든 인덱스 데이터
  const allIndices = [...koreaIndices, ...usIndices];
  if (fx) allIndices.push(fx);

  if (error) {
    return (
      <Card className="w-full">
        <CardContent className="p-4">
          <div className="flex items-center justify-between">
            <div className="text-red-600">인덱스 데이터 연결 오류</div>
            <button 
              onClick={reconnect}
              className="px-3 py-1 bg-blue-500 text-white rounded text-sm hover:bg-blue-600"
            >
              재연결
            </button>
          </div>
        </CardContent>
      </Card>
    );
  }

  if (allIndices.length === 0) {
    return (
      <Card className="w-full">
        <CardContent className="p-4">
          <div className="flex items-center justify-center text-muted-foreground">
            {isConnected ? '인덱스 데이터 로딩 중...' : '연결 중...'}
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <Card className="w-full">
      <CardContent className="p-4">
        {/* 연결 상태 표시 */}
        <div className="flex items-center justify-between mb-3">
          <div className="flex items-center space-x-2">
            <div className={cn(
              "w-2 h-2 rounded-full",
              isConnected ? "bg-green-500" : "bg-red-500"
            )} />
            <span className="text-sm font-medium">
              {isConnected ? '실시간 인덱스' : '연결 끊김'}
            </span>
          </div>
          
          {/* 데이터 소스 정보 */}
          <div className="text-xs text-muted-foreground">
            {Object.keys(indices).length}개 지수 모니터링
          </div>
        </div>

        {/* 티커 스크롤 */}
        <div 
          ref={containerRef}
          className="flex space-x-4 overflow-hidden"
          style={{ scrollBehavior: 'smooth' }}
        >
          {/* 인덱스들을 두 번 반복하여 무한 스크롤 효과 */}
          {[...allIndices, ...allIndices].map((index, idx) => (
            <IndexChip key={`${index.symbol}-${idx}`} index={index} />
          ))}
        </div>

        {/* 마우스 호버 시 애니메이션 일시정지 */}
        <div 
          className="absolute inset-0"
          onMouseEnter={() => {
            if (animationRef.current) {
              cancelAnimationFrame(animationRef.current);
            }
          }}
          onMouseLeave={() => {
            if (containerRef.current) {
              animationRef.current = requestAnimationFrame(() => {
                // 애니메이션 재시작 로직
              });
            }
          }}
        />
      </CardContent>
    </Card>
  );
};

export default IndicesTicker; 