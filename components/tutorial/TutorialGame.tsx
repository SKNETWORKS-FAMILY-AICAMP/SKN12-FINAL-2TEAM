"use client"

import { useState } from "react"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Progress } from "@/components/ui/progress"

const tutorialSteps = [
  {
    id: 1,
    title: "Welcome to Giga Buffett!",
    content: "I'm your AI guide, here to help you learn about investing. Let's start with the basics!",
  },
  {
    id: 2,
    title: "Understanding Stocks",
    content: "A stock represents ownership in a company. When you buy a stock, you become a shareholder.",
  },
  {
    id: 3,
    title: "Reading Stock Charts",
    content: "Stock charts show how a stock's price has changed over time. You can use them to identify trends.",
  },
  {
    id: 4,
    title: "Portfolio Diversification",
    content: "Diversifying your portfolio means investing in different types of assets to reduce risk.",
  },
  {
    id: 5,
    title: "Risk Management",
    content: "Managing risk involves understanding your risk tolerance and making informed decisions.",
  },
]

export default function TutorialGame() {
  const [currentStep, setCurrentStep] = useState(1)
  const progress = (currentStep / tutorialSteps.length) * 100

  const handleNextStep = () => {
    if (currentStep < tutorialSteps.length) {
      setCurrentStep(currentStep + 1)
    }
  }

  const handlePrevStep = () => {
    if (currentStep > 1) {
      setCurrentStep(currentStep - 1)
    }
  }

  return (
    <div className="flex flex-col items-center justify-center h-full">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>
            Level {currentStep} / {tutorialSteps.length}
          </CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center gap-4 p-4">
          <Progress value={progress} className="w-full" />
          <div className="text-center">
            <h2 className="text-2xl font-bold mb-4">{tutorialSteps[currentStep - 1].title}</h2>
            <p className="text-gray-600">{tutorialSteps[currentStep - 1].content}</p>
          </div>
          <div className="flex gap-4">
            <Button onClick={handlePrevStep} disabled={currentStep === 1}>
              Previous
            </Button>
            <Button onClick={handleNextStep} disabled={currentStep === tutorialSteps.length}>
              Next
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  )
}
