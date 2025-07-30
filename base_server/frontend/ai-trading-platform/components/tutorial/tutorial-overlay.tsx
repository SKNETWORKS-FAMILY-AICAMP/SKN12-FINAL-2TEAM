'use client';

import React, { useEffect, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card, CardContent } from '@/components/ui/card';
import { X, ChevronRight, ChevronLeft } from 'lucide-react';

interface TutorialStep {
  id: number;
  title: string;
  description: string;
  action?: string;
  target?: string;
}

interface TutorialOverlayProps {
  isVisible: boolean;
  stepInfo: TutorialStep | null;
  onNext: () => void;
  onPrevious: () => void;
  onSkip: () => void;
  currentStep: number;
  totalSteps: number;
}

export function TutorialOverlay({
  isVisible,
  stepInfo,
  onNext,
  onPrevious,
  onSkip,
  currentStep,
  totalSteps
}: TutorialOverlayProps) {
  const [targetElement, setTargetElement] = useState<HTMLElement | null>(null);
  const [overlayPosition, setOverlayPosition] = useState({ top: 0, left: 0, width: 0, height: 0 });

  // 타겟 요소 찾기 및 위치 계산
  useEffect(() => {
    if (!isVisible || !stepInfo?.target) {
      setTargetElement(null);
      return;
    }

    const element = document.querySelector(stepInfo.target) as HTMLElement;
    if (element) {
      setTargetElement(element);
      
      const rect = element.getBoundingClientRect();
      setOverlayPosition({
        top: rect.top + window.scrollY,
        left: rect.left + window.scrollX,
        width: rect.width,
        height: rect.height
      });

      // 타겟 요소 하이라이트 제거
      // element.style.outline = '2px solid #3b82f6';
      // element.style.outlineOffset = '2px';
      // element.style.zIndex = '9998';

      return () => {
        // element.style.outline = '';
        // element.style.outlineOffset = '';
        // element.style.zIndex = '';
      };
    }
  }, [isVisible, stepInfo?.target]);

  // 튜토리얼 활성화 시 스크롤 방지
  useEffect(() => {
    if (isVisible) {
      // body 스크롤 방지
      document.body.style.overflow = 'hidden';
      document.body.style.position = 'fixed';
      document.body.style.width = '100%';
      
      return () => {
        // 튜토리얼 종료 시 스크롤 복원
        document.body.style.overflow = '';
        document.body.style.position = '';
        document.body.style.width = '';
      };
    }
  }, [isVisible]);

  if (!isVisible || !stepInfo) {
    return null;
  }

  return (
    <>
      {/* 전체 화면 오버레이 */}
      <div 
        className="fixed inset-0 bg-black/50 z-[9999]"
        style={{ pointerEvents: 'auto' }}
        onClick={(e) => e.stopPropagation()}
      >
        {/* 타겟 요소 하이라이트 제거 */}
        {/* {targetElement && (
          <div
            className="absolute border-2 border-blue-500 rounded-md bg-blue-500/10"
            style={{
              top: overlayPosition.top - 4,
              left: overlayPosition.left - 4,
              width: overlayPosition.width + 8,
              height: overlayPosition.height + 8,
              zIndex: 9999,
              pointerEvents: 'none'
            }}
          />
        )} */}

        {/* 튜토리얼 카드 */}
        <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 z-[10000]">
          <Card className="w-96 max-w-[90vw] shadow-2xl border-2 border-transparent bg-gradient-to-br from-gray-950 via-slate-900 to-slate-950 text-white">
            <CardContent className="p-6">
              {/* 헤더 */}
              <div className="flex items-center justify-between mb-4">
                <div className="flex items-center space-x-2">
                  <div className="w-2 h-2 bg-blue-400 rounded-full animate-pulse" />
                  <span className="text-sm font-medium text-blue-400">
                    튜토리얼 {currentStep + 1} / {totalSteps}
                  </span>
                </div>
                <Button
                  variant="ghost"
                  size="sm"
                  onClick={onSkip}
                  className="h-8 w-8 p-0 hover:bg-gray-900 text-gray-400 hover:text-white"
                >
                  <X className="h-4 w-4" />
                </Button>
              </div>

              {/* 제목 */}
              <h3 className="text-lg font-semibold text-white mb-2">
                {stepInfo.title}
              </h3>

              {/* 설명 */}
              <p className="text-gray-400 mb-6 leading-relaxed">
                {stepInfo.description}
              </p>

              {/* 진행 바 */}
              <div className="w-full bg-gray-900 rounded-full h-2 mb-4">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all duration-300"
                  style={{ width: `${((currentStep + 1) / totalSteps) * 100}%` }}
                />
              </div>

              {/* 버튼 */}
              <div className="flex justify-between items-center">
                <Button
                  variant="outline"
                  onClick={onSkip}
                  className="text-gray-400 border-slate-700 hover:bg-slate-800 hover:text-white hover:border-slate-600 transition-all duration-200"
                >
                  건너뛰기
                </Button>
                
                <div className="flex items-center space-x-2">
                  <Button
                    variant="outline"
                    onClick={onPrevious}
                    disabled={currentStep === 0}
                    className="text-gray-400 border-slate-700 hover:bg-slate-800 hover:text-white hover:border-slate-600 disabled:opacity-50 disabled:cursor-not-allowed transition-all duration-200"
                  >
                    <ChevronLeft className="mr-2 h-4 w-4" />
                    이전
                  </Button>
                  
                  <Button
                    onClick={onNext}
                    className="bg-blue-600 hover:bg-blue-700 text-white border-blue-600 transition-all duration-200"
                  >
                    {currentStep + 1 === totalSteps ? '완료' : '다음'}
                    <ChevronRight className="ml-2 h-4 w-4" />
                  </Button>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </>
  );
} 