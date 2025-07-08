"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

const questions = [
  {
    id: 1,
    title: "투자 경험이 어느 정도인가요?",
    options: [
      { value: "beginner", label: "초보자", desc: "투자를 처음 시작합니다" },
      { value: "intermediate", label: "중급자", desc: "몇 년간 투자 경험이 있습니다" },
      { value: "advanced", label: "고급자", desc: "전문적인 투자 지식을 보유하고 있습니다" },
    ],
  },
  {
    id: 2,
    title: "선호하는 투자 스타일은?",
    options: [
      { value: "longterm", label: "장기투자", desc: "안정적인 장기 성장을 추구합니다" },
      { value: "shortterm", label: "단기투자", desc: "빠른 수익 실현을 선호합니다" },
      { value: "mixed", label: "혼합형", desc: "장단기를 적절히 조합합니다" },
    ],
  },
  {
    id: 3,
    title: "위험 감수 성향은?",
    options: [
      { value: "conservative", label: "보수적", desc: "안전한 투자를 선호합니다" },
      { value: "moderate", label: "중간", desc: "적당한 위험을 감수할 수 있습니다" },
      { value: "aggressive", label: "공격적", desc: "높은 수익을 위해 위험을 감수합니다" },
    ],
  },
  {
    id: 4,
    title: "월 투자 예산은?",
    options: [
      { value: "low", label: "50만원 이하", desc: "소액으로 시작하고 싶습니다" },
      { value: "medium", label: "50-200만원", desc: "적당한 금액을 투자하겠습니다" },
      { value: "high", label: "200만원 이상", desc: "적극적으로 투자하겠습니다" },
    ],
  },
  {
    id: 5,
    title: "투자 목표는?",
    options: [
      { value: "retirement", label: "은퇴 준비", desc: "노후 자금 마련이 목표입니다" },
      { value: "wealth", label: "자산 증식", desc: "재산을 늘리고 싶습니다" },
      { value: "income", label: "부수입", desc: "추가 수입원을 만들고 싶습니다" },
    ],
  },
]

export default function OnboardingSurvey({ onComplete }: { onComplete: (data: any) => void }) {
  const [currentQuestion, setCurrentQuestion] = useState(0)
  const [answers, setAnswers] = useState<Record<number, string>>({})
  const [selectedOption, setSelectedOption] = useState<string>("")

  const progress = ((currentQuestion + 1) / questions.length) * 100

  const handleNext = () => {
    if (selectedOption) {
      setAnswers((prev) => ({ ...prev, [currentQuestion]: selectedOption }))

      if (currentQuestion < questions.length - 1) {
        setCurrentQuestion(currentQuestion + 1)
        setSelectedOption("")
      } else {
        const finalAnswers = { ...answers, [currentQuestion]: selectedOption }
        onComplete(finalAnswers)
      }
    }
  }

  const handleBack = () => {
    if (currentQuestion > 0) {
      setCurrentQuestion(currentQuestion - 1)
      setSelectedOption(answers[currentQuestion - 1] || "")
    }
  }

  const currentQ = questions[currentQuestion]

  return (
    <div className="min-h-screen bg-gradient-to-br from-black via-gray-900 to-slate-900 flex items-center justify-center p-4 animate-fade-in">
      <div className="max-w-2xl w-full animate-slide-up">
        {/* 프로그레스 바 */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h1 className="text-2xl font-bold text-white">프로필 설정</h1>
            <span className="text-sm text-gray-400">
              {currentQuestion + 1} / {questions.length}
            </span>
          </div>
          <Progress value={progress} className="h-3 bg-gray-800" />
          <div className="flex justify-between mt-2">
            <span className="text-xs text-gray-500">시작</span>
            <span className="text-xs text-gray-500">{Math.round(progress)}% 완료</span>
            <span className="text-xs text-gray-500">완료</span>
          </div>
        </div>

        <Card className="shadow-2xl border-0 bg-gray-800/50 backdrop-blur-sm border border-gray-700/50">
          <CardHeader className="text-center pb-4">
            <CardTitle className="text-2xl font-bold text-white">{currentQ.title}</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {currentQ.options.map((option) => (
              <button
                key={option.value}
                onClick={() => setSelectedOption(option.value)}
                className={`w-full p-6 text-left rounded-xl border-2 transition-all transform hover:scale-105 duration-300 ${
                  selectedOption === option.value
                    ? "border-green-500 bg-green-500/20 shadow-lg shadow-green-500/25"
                    : "border-gray-700 bg-gray-800/50 hover:border-blue-500 hover:shadow-md hover:bg-gray-700/50"
                }`}
              >
                <div className="flex items-center justify-between">
                  <div>
                    <h3 className="font-semibold text-lg text-white">{option.label}</h3>
                    <p className="text-gray-300 mt-1">{option.desc}</p>
                  </div>
                  <div
                    className={`w-6 h-6 rounded-full border-2 transition-all duration-300 ${
                      selectedOption === option.value
                        ? "border-green-500 bg-green-500 shadow-lg shadow-green-500/50"
                        : "border-gray-400"
                    }`}
                  >
                    {selectedOption === option.value && (
                      <div className="w-full h-full flex items-center justify-center">
                        <span className="text-white text-sm">✓</span>
                      </div>
                    )}
                  </div>
                </div>
              </button>
            ))}

            <div className="flex justify-between pt-6">
              <Button
                onClick={handleBack}
                disabled={currentQuestion === 0}
                variant="outline"
                className="px-8 py-3 bg-transparent border-gray-700 text-gray-300 hover:bg-gray-800/50 hover:text-white hover:border-gray-600 transition-all duration-300"
              >
                이전
              </Button>
              <Button
                onClick={handleNext}
                disabled={!selectedOption}
                className="bg-gradient-to-r from-green-500 to-blue-500 hover:from-green-600 hover:to-blue-600 text-white px-8 py-3 transition-all duration-300 hover:shadow-lg"
              >
                {currentQuestion === questions.length - 1 ? "완료" : "다음"}
              </Button>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}
