"use client"

import { useState } from "react"
import { QuestionMarkCircleIcon } from "@heroicons/react/24/outline"
import { Button } from "@/components/ui/button"

interface HelpButtonProps {
  onShowTutorial: () => void
}

export default function HelpButton({ onShowTutorial }: HelpButtonProps) {
  const [isHovered, setIsHovered] = useState(false)

  return (
    <div className="fixed bottom-6 right-6 z-40">
      <Button
        onClick={onShowTutorial}
        onMouseEnter={() => setIsHovered(true)}
        onMouseLeave={() => setIsHovered(false)}
        className="w-14 h-14 rounded-full bg-gradient-to-r from-blue-500 to-purple-600 hover:from-blue-600 hover:to-purple-700 shadow-lg hover:shadow-xl transform transition-all duration-300 hover:scale-110"
      >
        <QuestionMarkCircleIcon className="w-6 h-6 text-white" />
      </Button>

      {isHovered && (
        <div className="absolute bottom-16 right-0 bg-gray-800 text-white px-3 py-2 rounded-lg text-sm whitespace-nowrap animate-fade-in">
          도움말 보기
          <div className="absolute top-full right-4 w-0 h-0 border-l-4 border-r-4 border-t-4 border-l-transparent border-r-transparent border-t-gray-800"></div>
        </div>
      )}
    </div>
  )
}
