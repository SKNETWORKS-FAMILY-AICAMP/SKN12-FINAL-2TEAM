"use client";
import { useCallback, useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/hooks/use-auth";

export default function LandingPage() {
  const { user, isLoading } = useAuth();
  const router = useRouter();
  const [loadingKey, setLoadingKey] = useState<number>(0);

  const navigateWithProgress = useCallback((path: string) => {
    setLoadingKey((prev) => prev + 1);
    setTimeout(() => {
      router.push(path);
    }, 2000);
  }, [router]);

  useEffect(() => {
    if (!isLoading && user) {
      router.replace("/dashboard");
    }
  }, [user, isLoading, router]);

  if (isLoading) return null;
  if (user) return null;

  return (
    <>
      <div className="loading-bar" key={loadingKey}></div>
      <header className="header">
        <div className="container">
          <div className="header-content">
            <div className="logo">
              <div className="logo-icon">📊</div>
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
                onClick={() => navigateWithProgress("/auth/login")}
              >
                Login
              </button>
              <button
                className="btn btn-primary"
                onClick={() => navigateWithProgress("/auth/register")}
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
                  onClick={() => navigateWithProgress("/auth/login")}
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
            최첨단 AI 기술과 직관적인 인터페이스로 설계된 전문 트레이딩 도구들
          </p>
          <div className="features-grid">
            <div className="feature-card">
              <div className="feature-icon">🤖</div>
              <h3 className="feature-title">AI-Powered Analysis</h3>
              <p className="feature-description">
                머신러닝 기반 시장 분석으로 패턴을 인식하고 최적의 매매 타이밍을 제안합니다.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">⚡</div>
              <h3 className="feature-title">Real-time Execution</h3>
              <p className="feature-description">
                밀리초 단위의 초고속 주문 실행으로 시장 기회를 놓치지 않습니다.
              </p>
            </div>
            <div className="feature-card">
              <div className="feature-icon">🛡️</div>
              <h3 className="feature-title">Risk Management</h3>
              <p className="feature-description">
                지능형 리스크 관리 시스템으로 포트폴리오를 안전하게 보호합니다.
              </p>
            </div>
          </div>
        </div>
      </section>
    </>
  );
}