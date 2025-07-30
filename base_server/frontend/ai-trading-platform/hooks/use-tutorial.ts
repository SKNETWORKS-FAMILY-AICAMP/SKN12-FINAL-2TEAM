import { useState, useEffect, useCallback } from 'react';

interface TutorialStep {
  id: number;
  title: string;
  description: string;
  action?: string;
  target?: string;
}

interface TutorialConfig {
  OVERVIEW: TutorialStep[];
  PORTFOLIO: TutorialStep[];
  SIGNALS: TutorialStep[];
  CHAT: TutorialStep[];
  SETTINGS: TutorialStep[];
}

const TUTORIAL_CONFIG: TutorialConfig = {
  OVERVIEW: [
    { id: 1, title: "환영합니다!", description: "AI Trader Pro에 오신 것을 환영합니다. 대시보드에서 주요 기능들을 확인해보세요." },
    { id: 2, title: "오늘의 주식 추천", description: "AI가 분석한 오늘의 주식 추천을 확인하세요. 실시간으로 업데이트되는 투자 기회를 놓치지 마세요.", target: ".stock-recommendation-card" },
    { id: 3, title: "마켓 오버뷰", description: "전체 시장 동향과 주요 지표를 한눈에 확인할 수 있습니다.", target: ".market-overview-card" },
    { id: 4, title: "포트폴리오 브레이크다운", description: "현재 포트폴리오의 자산 분포와 성과를 상세히 분석해보세요.", target: ".portfolio-breakdown-card" },
    { id: 5, title: "AI 시그널", description: "AI가 분석한 실시간 투자 시그널을 확인하세요.", target: ".ai-signal-card" },
    { id: 6, title: "완료!", description: "대시보드 튜토리얼을 완료했습니다. 이제 다른 페이지들을 탐험해보세요!" }
  ],
  PORTFOLIO: [
    { id: 1, title: "포트폴리오 관리", description: "포트폴리오 페이지에서 투자 현황을 자세히 확인할 수 있습니다." },
    { id: 2, title: "성과 분석", description: "포트폴리오 성과를 차트로 확인하고 분석해보세요.", target: ".portfolio-chart" },
    { id: 3, title: "완료!", description: "포트폴리오 튜토리얼을 완료했습니다!" }
  ],
  SIGNALS: [
    { id: 1, title: "AI 시그널", description: "AI가 분석한 투자 시그널을 확인하고 자동매매를 설정할 수 있습니다." },
    { id: 2, title: "시그널 추가", description: "새로운 시그널을 추가하여 자동매매를 시작해보세요.", target: "[data-tutorial='add-signal']" },
    { id: 3, title: "완료!", description: "시그널 튜토리얼을 완료했습니다!" }
  ],
  CHAT: [
    { id: 1, title: "AI 채팅", description: "AI와 대화하며 투자 상담을 받을 수 있습니다." },
    { id: 2, title: "새 채팅", description: "새로운 채팅을 시작해보세요.", target: ".chat-new-button" },
    { id: 3, title: "메시지 영역", description: "여기서 AI와의 대화를 확인할 수 있습니다.", target: ".chat-messages-area" },
    { id: 4, title: "완료!", description: "채팅 튜토리얼을 완료했습니다!" }
  ],
  SETTINGS: [
    { id: 1, title: "설정", description: "개인 정보와 앱 설정을 관리할 수 있습니다." },
    { id: 2, title: "프로필 설정", description: "프로필 정보를 수정하고 관리하세요." },
    { id: 3, title: "완료!", description: "설정 튜토리얼을 완료했습니다!" }
  ]
};

export function useTutorial() {
  const [currentTutorial, setCurrentTutorial] = useState<string | null>(null);
  const [currentStep, setCurrentStep] = useState(0);
  const [isLoading, setIsLoading] = useState(false);
  
  // 프론트엔드에서 관리하는 진행 상태 (백엔드와 동기화)
  const [progress, setProgress] = useState<Record<string, number>>({
    OVERVIEW: 0,
    PORTFOLIO: 0,
    SIGNALS: 0,
    CHAT: 0,
    SETTINGS: 0
  });

  // 현재 스텝 정보 계산
  const currentStepInfo = useCallback(() => {
    if (!currentTutorial) return null;
    const tutorialSteps = TUTORIAL_CONFIG[currentTutorial as keyof TutorialConfig];
    if (!tutorialSteps || currentStep >= tutorialSteps.length) return null;
    return tutorialSteps[currentStep];
  }, [currentTutorial, currentStep]);

  // 백엔드에서 진행 상태 조회
  const fetchProgress = useCallback(async () => {
    try {
      setIsLoading(true);
      const accessToken = localStorage.getItem('accessToken');
      if (!accessToken) {
        console.warn('❌ accessToken이 없어서 튜토리얼 진행 상태를 조회할 수 없습니다.');
        return;
      }

      console.log('🔍 Fetching tutorial progress from backend...');
      
      const response = await fetch('/api/tutorial/progress', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          accessToken: accessToken,
          sequence: 0
        })
      });

      if (response.ok) {
        const responseText = await response.text();
        console.log('📊 Backend progress response:', responseText);
        
        let data;
        try {
          // 이중 JSON 인코딩 처리
          let parsedText = responseText;
          if (parsedText.startsWith('"') && parsedText.endsWith('"')) {
            parsedText = JSON.parse(parsedText);
          }
          data = JSON.parse(parsedText);
        } catch (error) {
          console.error('❌ JSON 파싱 실패:', error);
          return;
        }

        if (data.errorCode === 0 && data.progress_list && Array.isArray(data.progress_list)) {
          // 백엔드에서 받은 진행 상태로 업데이트
          const newProgress: Record<string, number> = {
            OVERVIEW: 0,
            PORTFOLIO: 0,
            SIGNALS: 0,
            CHAT: 0,
            SETTINGS: 0
          };

          data.progress_list.forEach((item: any) => {
            if (item.tutorial_type && typeof item.completed_step === 'number') {
              newProgress[item.tutorial_type] = item.completed_step;
              console.log(`📝 Loaded progress: ${item.tutorial_type} = ${item.completed_step}`);
            }
          });

          console.log('✅ Updated progress from backend:', newProgress);
          setProgress(newProgress);
        } else {
          console.log('⚠️ 백엔드에서 진행 상태를 가져올 수 없습니다. 기본값 사용');
          console.log('Debug - data:', data);
          console.log('Debug - errorCode:', data.errorCode);
          console.log('Debug - progress_list:', data.progress_list);
        }
      } else {
        console.warn('❌ 백엔드 조회 실패. 기본값 사용');
      }
    } catch (error) {
      console.error('❌ 튜토리얼 진행 상태 조회 실패:', error);
    } finally {
      setIsLoading(false);
    }
  }, []);

  // 스텝 완료 저장 (백엔드에 저장)
  const completeStep = useCallback(async (tutorialType: string, stepNumber: number) => {
    try {
      const accessToken = localStorage.getItem('accessToken');
      if (!accessToken) {
        console.warn('accessToken이 없어서 백엔드에 저장할 수 없습니다.');
        return true; // 프론트엔드에서는 완료로 처리
      }

      console.log('💾 Saving to backend:', tutorialType, stepNumber);
      
      const response = await fetch('/api/tutorial/complete/step', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'Authorization': `Bearer ${accessToken}`
        },
        body: JSON.stringify({
          accessToken: accessToken,
          sequence: 0,
          tutorial_type: tutorialType,
          step_number: stepNumber
        })
      });

      if (response.ok) {
        const responseText = await response.text();
        console.log('📊 Complete step response:', responseText);
        
        let data;
        try {
          // 이중 JSON 인코딩 처리
          let parsedText = responseText;
          if (parsedText.startsWith('"') && parsedText.endsWith('"')) {
            parsedText = JSON.parse(parsedText);
          }
          data = JSON.parse(parsedText);
        } catch (error) {
          console.error('❌ JSON 파싱 실패:', error);
          return true;
        }
        
        if (data.errorCode === 0) {
          console.log('✅ Tutorial step saved to backend successfully');
          return true;
        } else {
          console.warn('⚠️ 백엔드 저장 실패했지만 프론트엔드에서는 완료로 처리합니다.');
          return true;
        }
      } else {
        console.warn('❌ 백엔드 저장 실패했지만 프론트엔드에서는 완료로 처리합니다.');
        return true;
      }

      return true;
    } catch (error) {
      console.error('튜토리얼 스텝 완료 처리 실패:', error);
      return true; // 에러가 발생해도 프론트엔드 상태는 업데이트
    }
  }, []);

  // 튜토리얼 시작
  const startTutorial = useCallback((tutorialType: string) => {
    console.log('🚀 Starting tutorial:', tutorialType);
    const tutorialSteps = TUTORIAL_CONFIG[tutorialType as keyof TutorialConfig];
    if (tutorialSteps) {
      setCurrentTutorial(tutorialType);
      setCurrentStep(progress[tutorialType] || 0);
    }
  }, [progress]);

  // 다음 스텝으로 진행
  const nextStep = useCallback(async () => {
    if (!currentTutorial) return;

    const tutorialSteps = TUTORIAL_CONFIG[currentTutorial as keyof TutorialConfig];
    const totalSteps = tutorialSteps ? tutorialSteps.length : 0;
    const nextStepNumber = currentStep + 1;

    console.log('📝 Completing step:', currentTutorial, nextStepNumber, 'of', totalSteps);

    // 프론트엔드 상태 즉시 업데이트
    setProgress(prev => {
      const newProgress = { ...prev, [currentTutorial]: Math.max(prev[currentTutorial] || 0, nextStepNumber) };
      console.log('Updated frontend progress:', newProgress);
      return newProgress;
    });

    // 백엔드에 저장
    const success = await completeStep(currentTutorial, nextStepNumber);

    if (success) {
      if (nextStepNumber >= totalSteps) {
        // 튜토리얼 완료
        console.log('✅ Tutorial completed:', currentTutorial);
        setCurrentTutorial(null);
        setCurrentStep(0);
      } else {
        // 다음 스텝으로 이동
        setCurrentStep(nextStepNumber);
      }
    }
  }, [currentTutorial, currentStep, completeStep]);

  // 이전 스텝으로 이동
  const previousStep = useCallback(() => {
    if (!currentTutorial || currentStep <= 0) return;
    
    console.log('⬅️ Going to previous step:', currentTutorial, currentStep - 1);
    setCurrentStep(currentStep - 1);
  }, [currentTutorial, currentStep]);

  // 튜토리얼 건너뛰기
  const skipTutorial = useCallback(async () => {
    if (!currentTutorial) return;
    
    console.log('⏭️ Skipping tutorial:', currentTutorial);
    const tutorialSteps = TUTORIAL_CONFIG[currentTutorial as keyof TutorialConfig];
    const totalSteps = tutorialSteps ? tutorialSteps.length : 0;
    
    // 백엔드에 모든 단계 완료로 저장
    const success = await completeStep(currentTutorial, totalSteps);
    
    if (success) {
      // 프론트엔드 상태도 완료로 업데이트
      setProgress(prev => ({ ...prev, [currentTutorial]: totalSteps }));
      console.log('✅ Tutorial skipped and completed:', currentTutorial);
    }
    
    setCurrentTutorial(null);
    setCurrentStep(0);
  }, [currentTutorial, completeStep]);

  // 페이지 로드 시 진행 상태 조회
  useEffect(() => {
    console.log('🔄 Initial tutorial progress fetch');
    fetchProgress();
  }, [fetchProgress]);

  // 진행 상태가 로드된 후 튜토리얼 시작
  useEffect(() => {
    if (isLoading) {
      console.log('⏳ Progress still loading, waiting...');
      return;
    }

    const currentPath = window.location.pathname;
    const tutorialMap: Record<string, string> = {
      '/dashboard': 'OVERVIEW',
      '/portfolio': 'PORTFOLIO',
      '/autotrade': 'SIGNALS',
      '/chat': 'CHAT',
      '/settings': 'SETTINGS'
    };
    const tutorialType = tutorialMap[currentPath];

    if (tutorialType && !currentTutorial) {
      const currentProgress = progress[tutorialType] || 0;
      const tutorialSteps = TUTORIAL_CONFIG[tutorialType as keyof TutorialConfig];
      const totalSteps = tutorialSteps ? tutorialSteps.length : 0;

      console.log('🎯 Tutorial check:', {
        tutorialType,
        currentProgress,
        totalSteps,
        shouldStart: currentProgress < totalSteps && totalSteps > 0
      });

      // 완료되지 않은 튜토리얼만 시작
      if (currentProgress < totalSteps && totalSteps > 0) {
        const delay = currentPath === '/dashboard' ? 3000 : 2000;
        const timeoutId = setTimeout(() => {
          if (!currentTutorial) { // 중복 실행 방지
            startTutorial(tutorialType);
          }
        }, delay);
        
        return () => clearTimeout(timeoutId);
      } else {
        console.log('✅ Tutorial already completed:', tutorialType);
      }
    }
  }, [isLoading, progress, currentTutorial, startTutorial]);

  return {
    currentTutorial,
    currentStep,
    currentStepInfo,
    nextStep,
    previousStep, // 추가된 함수
    skipTutorial,
    isLoading,
    progress
  };
} 