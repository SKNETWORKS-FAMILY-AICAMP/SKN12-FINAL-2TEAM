"use client"

import { useState } from "react"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"
import { TutorialCard } from "@/components/tutorial/tutorial-card"
import { LearningPath } from "@/components/tutorial/learning-path"
import { BookOpen, Play, Star, Trophy, Target } from "lucide-react"

const learningPaths = [
  {
    id: 1,
    title: "트레이딩 기초",
    description: "투자의 기본 개념부터 차트 읽는 법까지",
    progress: 75,
    lessons: 12,
    duration: "2시간",
    level: "초급",
    icon: BookOpen,
    color: "from-blue-500 to-indigo-600",
  },
  {
    id: 2,
    title: "AI 트레이딩 활용",
    description: "AI 도구를 활용한 스마트 투자 전략",
    progress: 45,
    lessons: 8,
    duration: "1.5시간",
    level: "중급",
    icon: Target,
    color: "from-purple-500 to-pink-600",
  },
  {
    id: 3,
    title: "리스크 관리",
    description: "안전한 투자를 위한 리스크 관리 방법",
    progress: 20,
    lessons: 10,
    duration: "2.5시간",
    level: "고급",
    icon: Trophy,
    color: "from-orange-500 to-red-600",
  },
]

const quickTutorials = [
  {
    title: "첫 거래 시작하기",
    duration: "5분",
    type: "video",
    completed: true,
  },
  {
    title: "AI 시그널 해석하기",
    duration: "8분",
    type: "interactive",
    completed: false,
  },
  {
    title: "포트폴리오 분석하기",
    duration: "6분",
    type: "guide",
    completed: false,
  },
  {
    title: "자동매매 설정하기",
    duration: "12분",
    type: "video",
    completed: false,
  },
]

export default function TutorialPage() {
  const [selectedPath, setSelectedPath] = useState<number | null>(null)

  return (
    <div className="space-y-8">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">학습 센터</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">전문가가 되는 여정을 시작하세요</p>
        </div>
        <div className="flex items-center gap-3">
          <Badge variant="outline" className="bg-yellow-50 text-yellow-700 border-yellow-200">
            <Star className="w-4 h-4 mr-1" />
            레벨 3
          </Badge>
          <Badge variant="outline" className="bg-green-50 text-green-700 border-green-200">
            <Trophy className="w-4 h-4 mr-1" />
            15개 완료
          </Badge>
        </div>
      </div>

      {/* Progress Overview */}
      <Card className="border-0 bg-gradient-to-r from-purple-500 via-pink-500 to-orange-500 text-white professional-shadow">
        <CardContent className="p-8">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">67%</div>
              <p className="text-purple-100">전체 진행률</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">15</div>
              <p className="text-purple-100">완료한 레슨</p>
            </div>
            <div className="text-center">
              <div className="text-3xl font-bold mb-2">8.5시간</div>
              <p className="text-purple-100">학습 시간</p>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Learning Paths */}
      <div className="space-y-6">
        <h2 className="text-2xl font-bold text-gray-900 dark:text-white">학습 경로</h2>
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
          {learningPaths.map((path) => (
            <LearningPath
              key={path.id}
              path={path}
              isSelected={selectedPath === path.id}
              onSelect={() => setSelectedPath(path.id)}
            />
          ))}
        </div>
      </div>

      {/* Quick Tutorials */}
      <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-green-500 to-emerald-600 text-white">
              <Play className="h-5 w-5" />
            </div>
            빠른 튜토리얼
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {quickTutorials.map((tutorial, index) => (
              <TutorialCard key={index} tutorial={tutorial} />
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Achievement Section */}
      <Card className="border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
        <CardHeader className="pb-4">
          <CardTitle className="flex items-center gap-3">
            <div className="p-2 rounded-lg bg-gradient-to-br from-yellow-500 to-orange-600 text-white">
              <Trophy className="h-5 w-5" />
            </div>
            성취 배지
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            {[
              { name: "첫 거래", icon: "🎯", earned: true },
              { name: "연속 학습", icon: "🔥", earned: true },
              { name: "AI 마스터", icon: "🤖", earned: false },
              { name: "리스크 관리자", icon: "🛡️", earned: false },
            ].map((badge, index) => (
              <div
                key={index}
                className={`p-4 rounded-xl text-center transition-all duration-300 ${
                  badge.earned
                    ? "bg-gradient-to-br from-yellow-50 to-orange-50 dark:from-yellow-900/20 dark:to-orange-900/20 border-2 border-yellow-200 dark:border-yellow-700"
                    : "bg-gray-50 dark:bg-slate-700/50 border-2 border-gray-200 dark:border-gray-600 opacity-50"
                }`}
              >
                <div className="text-3xl mb-2">{badge.icon}</div>
                <p className="text-sm font-medium text-gray-900 dark:text-white">{badge.name}</p>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
