"use client"

import { useAuth } from "@/hooks/use-auth"
import { useRouter } from "next/navigation"
import { useEffect } from "react"

export default function HomePage() {
  const { user, isLoading } = useAuth()
  const router = useRouter()

  useEffect(() => {
    if (!isLoading && user) {
      router.push("/dashboard")
    }
  }, [user, isLoading, router])

  if (isLoading) return null
  if (user) return null

  // 랜딩 페이지 UI 직접 렌더링
  return (
    <>
      <div className="loading-bar"></div>
      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="logo">
              <span>AI Trader Pro</span>
            </div>
            <nav className="nav">
              <a href="#features">Features</a>
              <a href="#pricing">Pricing</a>
              <a href="#about">About</a>
              <a href="#contact">Contact</a>
            </nav>
            <div className="auth-buttons">
              <button
                className="btn btn-secondary"
                onClick={() => router.push("/auth/login")}
              >
                Login
              </button>
              <button
                className="btn btn-primary"
                onClick={() => router.push("/auth/register")}
              >
                Get Started
              </button>
            </div>
          </div>
        </div>
      </header>
      <main className="main">
        <div className="container">
          <section className="hero">
            <div className="hero-content">
              <h1>
                Professional <span className="highlight">AI Trading</span> Platform
              </h1>
              <p>
                고급 AI 알고리즘과 실시간 시장 분석으로 스마트한 투자 결정을 내리세요. 전문가 수준의 트레이딩을 간단하게.
              </p>
              <div className="hero-actions">
                <button 
                  className="btn btn-primary btn-large"
                  onClick={() => router.push("/auth/login")}
                >
                  Start Trading
                </button>
                <a href="#" className="btn btn-secondary btn-large">View Demo</a>
              </div>
              <div className="stats">
                <div className="stat-item">
                  <div>
                    <div className="stat-number">94%</div>
                    <div className="stat-label">Success Rate</div>
                  </div>
                </div>
                <div className="stat-item">
                  <div>
                    <div className="stat-number">$2.4M</div>
                    <div className="stat-label">Volume Traded</div>
                  </div>
                </div>
                <div className="rating">
                  <div className="stars">★★★★★</div>
                  <span style={{ color: "rgba(255,255,255,0.7)" }}>4.9/5</span>
                </div>
              </div>
            </div>
            <div className="dashboard">
              <div className="dashboard-grid">
                <div className="metric-card">
                  <div className="metric-label">Portfolio Value</div>
                  <div className="metric-value">$847,296</div>
                  <div className="metric-change">
                    <span>↗</span>
                    <span>+18.4%</span>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Active Positions</div>
                  <div className="metric-value">12</div>
                  <div className="metric-change">
                    <span>↗</span>
                    <span>+3</span>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Monthly Return</div>
                  <div className="metric-value">24.7%</div>
                  <div className="metric-change">
                    <span>↗</span>
                    <span>+5.2%</span>
                  </div>
                </div>
                <div className="metric-card">
                  <div className="metric-label">Win Rate</div>
                  <div className="metric-value">87%</div>
                  <div className="metric-change">
                    <span>↗</span>
                    <span>+12%</span>
                  </div>
                </div>
                <div className="chart-visualization">
                  <div className="chart-line"></div>
                </div>
              </div>
            </div>
          </section>
        </div>
      </main>
      <section className="features" id="features">
        <div className="container">
          <h2 className="section-title">Advanced Trading Features</h2>
          <p className="section-subtitle">
            AI 기술과 금융 전문성을 결합한 핵심 트레이딩 솔루션
          </p>
          
          {/* Core Features Grid */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-8">
            <div className="text-center p-8 bg-gradient-to-br from-blue-600/20 to-blue-800/20 rounded-2xl border border-blue-500/30">
              <div className="text-5xl mb-4">🤖</div>
              <h3 className="text-xl font-semibold text-white mb-3">AI-Powered Analysis</h3>
              <p className="text-gray-300">
                GPT-4 기반 시장 분석으로 최적의 매매 타이밍을 제안합니다.
              </p>
            </div>
            
            <div className="text-center p-8 bg-gradient-to-br from-purple-600/20 to-purple-800/20 rounded-2xl border border-purple-500/30">
              <div className="text-5xl mb-4">⚡</div>
              <h3 className="text-xl font-semibold text-white mb-3">Real-time Execution</h3>
              <p className="text-gray-300">
                밀리초 단위 초고속 주문 실행으로 시장 기회를 놓치지 않습니다.
              </p>
            </div>
            
            <div className="text-center p-8 bg-gradient-to-br from-green-600/20 to-green-800/20 rounded-2xl border border-green-500/30">
              <div className="text-5xl mb-4">🛡️</div>
              <h3 className="text-xl font-semibold text-white mb-3">Risk Management</h3>
              <p className="text-gray-300">
                지능형 리스크 관리로 포트폴리오를 안전하게 보호합니다.
              </p>
            </div>
            
            <div className="text-center p-8 bg-gradient-to-br from-orange-600/20 to-orange-800/20 rounded-2xl border border-orange-500/30">
              <div className="text-5xl mb-4">🌍</div>
              <h3 className="text-xl font-semibold text-white mb-3">Global Markets</h3>
              <p className="text-gray-300">
                한국, 미국, 일본, 유럽 등 전 세계 주요 금융시장 접근.
              </p>
            </div>
            
            <div className="text-center p-8 bg-gradient-to-br from-red-600/20 to-red-800/20 rounded-2xl border border-red-500/30">
              <div className="text-5xl mb-4">📱</div>
              <h3 className="text-xl font-semibold text-white mb-3">Cross-Platform</h3>
              <p className="text-gray-300">
                웹, 모바일, 데스크톱에서 언제 어디서나 거래하세요.
              </p>
            </div>
            
            <div className="text-center p-8 bg-gradient-to-br from-cyan-600/20 to-cyan-800/20 rounded-2xl border border-cyan-500/30">
              <div className="text-5xl mb-4">🔔</div>
              <h3 className="text-xl font-semibold text-white mb-3">Smart Alerts</h3>
              <p className="text-gray-300">
                AI 기반 맞춤형 알림으로 중요한 시장 변화를 놓치지 마세요.
              </p>
            </div>
          </div>
        </div>
      </section>
      
      {/* Pricing Section */}
      <section className="features" id="pricing">
        <div className="container">
          <h2 className="section-title">Pricing Plans</h2>
          <p className="section-subtitle">
            투자 목표에 맞는 최적의 플랜을 선택하세요
          </p>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🆓</div>
              <h3 className="feature-title">Free Plan</h3>
              <div className="pricing-price">
                <span className="text-2xl font-bold text-blue-400">₩0</span>
                <span className="text-sm text-gray-400">/월</span>
              </div>
              <p className="feature-description">
                기본 AI 분석과 일일 10회 거래 신호를 제공합니다. 투자를 시작하기에 완벽한 플랜입니다.
              </p>
              <ul className="mt-4 space-y-2 text-sm text-gray-300">
                <li>✓ 기본 AI 분석</li>
                <li>✓ 일일 10회 거래 신호</li>
                <li>✓ 기본 차트 도구</li>
                <li>✓ 이메일 알림</li>
              </ul>
            </div>

            <div className="feature-card">
              <div className="feature-icon">⭐</div>
              <h3 className="feature-title">Pro Plan</h3>
              <div className="pricing-price">
                <span className="text-2xl font-bold text-green-400">₩99,000</span>
                <span className="text-sm text-gray-400">/월</span>
              </div>
              <p className="feature-description">
                고급 AI 분석과 무제한 거래 신호로 전문가 수준의 트레이딩을 경험하세요.
              </p>
              <ul className="mt-4 space-y-2 text-sm text-gray-300">
                <li>✓ 고급 AI 분석</li>
                <li>✓ 무제한 거래 신호</li>
                <li>✓ 실시간 시장 데이터</li>
                <li>✓ 포트폴리오 관리</li>
                <li>✓ 우선 고객 지원</li>
              </ul>
            </div>

            <div className="feature-card">
              <div className="feature-icon">🚀</div>
              <h3 className="feature-title">Enterprise</h3>
              <div className="pricing-price">
                <span className="text-2xl font-bold text-purple-400">₩299,000</span>
                <span className="text-sm text-gray-400">/월</span>
              </div>
              <p className="feature-description">
                전문가용 AI 모델과 맞춤형 전략 개발로 최고 수준의 트레이딩 성과를 달성하세요.
              </p>
              <ul className="mt-4 space-y-2 text-sm text-gray-300">
                <li>✓ 전문가용 AI 모델</li>
                <li>✓ 맞춤형 전략 개발</li>
                <li>✓ API 접근</li>
                <li>✓ 전담 매니저</li>
                <li>✓ 24/7 지원</li>
              </ul>
            </div>
          </div>
        </div>
      </section>
      
      {/* About Section */}
      <section className="features" id="about">
        <div className="container">
          <h2 className="section-title">About Us</h2>
          <p className="section-subtitle">
            AI 트레이딩의 미래를 만들어가는 혁신적인 팀
          </p>
          
          {/* Main Story */}
          <div className="mb-16 text-center max-w-4xl mx-auto">
            <p className="text-lg text-gray-300 leading-relaxed mb-8">
              2020년 설립 이후, 우리는 개인 투자자들이 전문가 수준의 투자 결정을 내릴 수 있도록 돕는 AI 트레이딩 플랫폼을 개발해왔습니다. 
              최첨단 머신러닝 기술과 금융 전문성을 결합하여, 누구나 쉽게 접근할 수 있는 스마트 투자 솔루션을 제공합니다.
            </p>
          </div>

          {/* Two Column Layout */}
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-12 mb-16">
            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <div className="text-2xl">🎯</div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Our Mission</h3>
                  <p className="text-gray-300">
                    금융 민주화를 통해 모든 사람이 AI의 힘을 활용하여 스마트한 투자 결정을 내릴 수 있도록 돕습니다.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="text-2xl">🔬</div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Technology</h3>
                  <p className="text-gray-300">
                    GPT-4, LSTM, Transformer 등 최신 AI 모델을 활용한 시장 예측 및 포트폴리오 최적화 기술을 보유하고 있습니다.
                  </p>
                </div>
              </div>
            </div>

            <div className="space-y-6">
              <div className="flex items-start space-x-4">
                <div className="text-2xl">👥</div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Our Team</h3>
                  <p className="text-gray-300">
                    금융공학 박사, AI 연구원, 전직 투자은행 트레이더, 소프트웨어 엔지니어로 구성된 15명의 전문가 팀입니다.
                  </p>
                </div>
              </div>
              
              <div className="flex items-start space-x-4">
                <div className="text-2xl">🌍</div>
                <div>
                  <h3 className="text-xl font-semibold text-white mb-2">Global Reach</h3>
                  <p className="text-gray-300">
                    한국, 미국, 일본, 유럽 등 전 세계 주요 금융시장에서 실시간 데이터를 수집하고 분석합니다.
              </p>
                </div>
              </div>
            </div>
          </div>
          
          {/* Company Stats - Wider Layout */}
          <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
            <div className="text-center p-6 bg-gray-800/30 rounded-lg border border-gray-700/50">
              <div className="text-4xl font-bold text-blue-400 mb-2">5+</div>
              <div className="text-sm text-gray-400">Years Experience</div>
            </div>
            <div className="text-center p-6 bg-gray-800/30 rounded-lg border border-gray-700/50">
              <div className="text-4xl font-bold text-green-400 mb-2">10K+</div>
              <div className="text-sm text-gray-400">Active Users</div>
            </div>
            <div className="text-center p-6 bg-gray-800/30 rounded-lg border border-gray-700/50">
              <div className="text-4xl font-bold text-purple-400 mb-2">$50M+</div>
              <div className="text-sm text-gray-400">Trading Volume</div>
            </div>
            <div className="text-center p-6 bg-gray-800/30 rounded-lg border border-gray-700/50">
              <div className="text-4xl font-bold text-orange-400 mb-2">99.9%</div>
              <div className="text-sm text-gray-400">Uptime</div>
            </div>
          </div>
        </div>
      </section>
      
      {/* Contact Section */}
      <section className="features" id="contact">
        <div className="container">
          <div className="text-center mb-12">
            <h2 className="text-5xl font-bold text-white mb-6">Let's Connect</h2>
            <p className="text-2xl text-gray-300 leading-relaxed">
              AI 트레이딩의 세계로 함께해요
            </p>
          </div>
          
          {/* Main Contact Container */}
          <div className="max-w-7xl mx-auto">
            <div className="relative">
              {/* Background Elements */}
              <div className="absolute -top-16 -left-16 w-32 h-32 bg-gradient-to-r from-blue-500/20 to-purple-500/20 rounded-full blur-xl"></div>
              <div className="absolute -bottom-16 -right-16 w-32 h-32 bg-gradient-to-r from-purple-500/20 to-pink-500/20 rounded-full blur-xl"></div>
              
              {/* Main Content */}
              <div className="relative bg-gradient-to-br from-gray-900/95 via-gray-800/95 to-gray-900/95 backdrop-blur-lg rounded-2xl border border-gray-700/50 overflow-hidden shadow-lg">
                
                {/* Top Decorative Bar */}
                <div className="h-1 bg-gradient-to-r from-blue-500 via-purple-500 to-pink-500"></div>
                
                {/* Contact Info Section */}
                <div className="p-8 flex items-center justify-center min-h-[400px]">
                  
                  {/* Simple Contact Info - 4 Essential Items */}
                  <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-6xl">
                    {/* Office Location */}
                    <div className="group relative text-center p-8 bg-gradient-to-br from-blue-600/20 to-blue-800/20 rounded-2xl border border-blue-500/30 hover:border-blue-400/50 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-blue-500/20">
                      <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-blue-600/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="relative">
                        <div className="w-20 h-20 bg-gradient-to-br from-blue-400 to-blue-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:shadow-xl group-hover:shadow-blue-500/30 transition-all duration-300">
                          <span className="text-3xl group-hover:scale-110 transition-transform duration-300">📍</span>
                        </div>
                        <h4 className="text-xl font-bold text-white mb-3 group-hover:text-blue-200 transition-colors">Office Location</h4>
                        <p className="text-blue-200 text-base mb-2 font-medium">AI Trading Center</p>
                        <p className="text-blue-100 text-sm leading-relaxed">서울 금천구 가산디지털1로 25 대륭테크노타운17차, 18층</p>
                      </div>
                    </div>
                    
                    {/* Email Contact */}
                    <div className="group relative text-center p-8 bg-gradient-to-br from-purple-600/20 to-purple-800/20 rounded-2xl border border-purple-500/30 hover:border-purple-400/50 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-purple-500/20">
                      <div className="absolute inset-0 bg-gradient-to-br from-purple-500/5 to-purple-600/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="relative">
                        <div className="w-20 h-20 bg-gradient-to-br from-purple-400 to-purple-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:shadow-xl group-hover:shadow-purple-500/30 transition-all duration-300">
                          <span className="text-3xl group-hover:scale-110 transition-transform duration-300">📧</span>
                        </div>
                        <h4 className="text-xl font-bold text-white mb-3 group-hover:text-purple-200 transition-colors">Email Contact</h4>
                        <p className="text-purple-200 text-base mb-2 font-medium">24/7 Support</p>
                        <a href="mailto:hello@aitrader.pro" className="text-purple-100 text-base hover:text-purple-200 transition-colors font-medium hover:underline">
                          qkrwlsdid987@gmail.com
                        </a>
                      </div>
                    </div>
                    
                    {/* Phone Support */}
                    <div className="group relative text-center p-8 bg-gradient-to-br from-green-600/20 to-green-800/20 rounded-2xl border border-green-500/30 hover:border-green-400/50 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-green-500/20">
                      <div className="absolute inset-0 bg-gradient-to-br from-green-500/5 to-green-600/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="relative">
                        <div className="w-20 h-20 bg-gradient-to-br from-green-400 to-green-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:shadow-xl group-hover:shadow-green-500/30 transition-all duration-300">
                          <span className="text-3xl group-hover:scale-110 transition-transform duration-300">📱</span>
                        </div>
                        <h4 className="text-xl font-bold text-white mb-3 group-hover:text-green-200 transition-colors">Phone Support</h4>
                        <p className="text-green-200 text-base mb-2 font-medium">Direct Line</p>
                        <a href="tel:+82-2-1234-5678" className="text-green-100 text-base hover:text-green-200 transition-colors font-medium hover:underline">
                          +82-10-3720-8454
                        </a>
                      </div>
                    </div>
                    
                    {/* Business Hours */}
                    <div className="group relative text-center p-8 bg-gradient-to-br from-orange-600/20 to-orange-800/20 rounded-2xl border border-orange-500/30 hover:border-orange-400/50 transition-all duration-300 hover:scale-105 hover:shadow-2xl hover:shadow-orange-500/20">
                      <div className="absolute inset-0 bg-gradient-to-br from-orange-500/5 to-orange-600/5 rounded-2xl opacity-0 group-hover:opacity-100 transition-opacity duration-300"></div>
                      <div className="relative">
                        <div className="w-20 h-20 bg-gradient-to-br from-orange-400 to-orange-600 rounded-2xl flex items-center justify-center mx-auto mb-6 shadow-lg group-hover:shadow-xl group-hover:shadow-orange-500/30 transition-all duration-300">
                          <span className="text-3xl group-hover:scale-110 transition-transform duration-300">🕒</span>
                        </div>
                        <h4 className="text-xl font-bold text-white mb-3 group-hover:text-orange-200 transition-colors">Business Hours</h4>
                        <div className="text-orange-200 text-sm space-y-2 leading-relaxed">
                          <p className="font-medium">평일: 09:00 - 18:00</p>
                          <p className="font-medium">주말: 10:00 - 16:00</p>
                          <p className="font-medium">공휴일: 휴무</p>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>
    </>
  )
}
