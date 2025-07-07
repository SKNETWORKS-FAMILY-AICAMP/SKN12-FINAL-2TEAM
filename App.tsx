"use client"

import { useState } from "react"
import Layout from "./components/common/Layout"
import Dashboard from "./components/dashboard/Dashboard"
import Portfolio from "./components/portfolio/Portfolio"
import AIChat from "./components/ai-chat/AIChat"
import AutoTrading from "./components/auto-trading/AutoTrading"
import Settings from "./components/settings/Settings"
import WelcomePage from "./components/welcome/WelcomePage"
import OnboardingSurvey from "./components/onboarding/OnboardingSurvey"
import LiveTutorial from "./components/tutorial/LiveTutorial"
import HelpButton from "./components/tutorial/HelpButton"

function App() {
  const [currentPage, setCurrentPage] = useState("welcome")
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [showTutorial, setShowTutorial] = useState(false)
  const [userProfile, setUserProfile] = useState(null)

  const handleGetStarted = () => {
    setCurrentPage("onboarding")
  }

  const handleOnboardingComplete = (surveyData: any) => {
    setUserProfile(surveyData)
    setIsAuthenticated(true)
    setCurrentPage("dashboard")
    setShowTutorial(true)
  }

  const handleTutorialComplete = () => {
    setShowTutorial(false)
  }

  const handleShowTutorial = () => {
    setShowTutorial(true)
  }

  const handlePageChange = (page: string) => {
    setCurrentPage(page)
  }

  if (!isAuthenticated) {
    switch (currentPage) {
      case "welcome":
        return <WelcomePage onGetStarted={handleGetStarted} />
      case "onboarding":
        return <OnboardingSurvey onComplete={handleOnboardingComplete} />
      default:
        return <WelcomePage onGetStarted={handleGetStarted} />
    }
  }

  const renderAuthenticatedPage = () => {
    switch (currentPage) {
      case "dashboard":
        return <Dashboard />
      case "portfolio":
        return <Portfolio />
      case "ai-chat":
        return <AIChat />
      case "auto-trading":
        return <AutoTrading />
      case "settings":
        return <Settings />
      default:
        return <Dashboard />
    }
  }

  return (
    <div className="relative">
      <Layout currentPage={currentPage} onPageChange={handlePageChange}>
        {renderAuthenticatedPage()}
      </Layout>

      {/* 도움말 버튼 */}
      {isAuthenticated && !showTutorial && <HelpButton onShowTutorial={handleShowTutorial} />}

      {/* 라이브 튜토리얼 */}
      {showTutorial && (
        <LiveTutorial
          onComplete={handleTutorialComplete}
          onPageChange={handlePageChange}
          userProfile={userProfile}
          currentPage={currentPage}
        />
      )}
    </div>
  )
}

export default App
