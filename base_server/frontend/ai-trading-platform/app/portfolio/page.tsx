"use client"

import React, { useState } from 'react';
import { TrendingUp, DollarSign, Percent, Clock, BarChart3, PieChart, History, Settings, ArrowLeft, Plus, Menu } from 'lucide-react';
import { useRouter } from 'next/navigation';
import { LineChart, Line, AreaChart, Area, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart as RechartsPieChart, Pie, Cell } from 'recharts';
import { Header } from "@/components/layout/header";
import { AppSidebar } from "@/components/layout/AppSidebar";

export default function PortfolioPage() {
  const router = useRouter();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  const stats = [
    {
      icon: DollarSign,
      title: '총 자산 가치',
      value: '₩125,847,230',
      change: '+₩13,847,230',
      percentage: '+12.5%',
      color: 'bg-emerald-500'
    },
    {
      icon: TrendingUp,
      title: '일일 손익',
      value: '+₩2,847,230',
      subtitle: '오늘',
      percentage: '+2.34%',
      color: 'bg-blue-500'
    },
    {
      icon: Percent,
      title: '총 수익률',
      value: '+18.7%',
      subtitle: '전체 기간',
      percentage: '목표 대비 +3.7%',
      color: 'bg-purple-500'
    },
    {
      icon: Clock,
      title: '포트폴리오 다양성',
      value: '8.2/10',
      subtitle: '우수',
      percentage: '리스크 분산',
      color: 'bg-orange-500'
    }
  ];

  // Performance chart data
  const performanceData = [
    { month: '1월', value: 100000000, return: 8.5 },
    { month: '2월', value: 98000000, return: -2.1 },
    { month: '3월', value: 110000000, return: 12.3 },
    { month: '4월', value: 116000000, return: 5.7 },
    { month: '5월', value: 122000000, return: 5.2 },
    { month: '6월', value: 118000000, return: -3.3 },
    { month: '7월', value: 125000000, return: 5.9 },
    { month: '8월', value: 132000000, return: 5.6 },
    { month: '9월', value: 128000000, return: -3.0 },
    { month: '10월', value: 135000000, return: 5.5 },
    { month: '11월', value: 142000000, return: 5.2 },
    { month: '12월', value: 125847230, return: -11.4 }
  ];

  // Pie chart data
  const pieData = [
    { name: '기술', value: 45, color: '#3B82F6' },
    { name: '금융', value: 25, color: '#10B981' },
    { name: '헬스케어', value: 20, color: '#8B5CF6' },
    { name: '기타', value: 10, color: '#6B7280' }
  ];

  const monthlyReturns = [
    { month: '1월', return: '+8.5%', positive: true },
    { month: '2월', return: '-2.1%', positive: false },
    { month: '3월', return: '+12.3%', positive: true },
    { month: '4월', return: '+5.7%', positive: true },
  ];

  const allocations = [
    { name: '기술', percentage: 45, color: 'bg-blue-500' },
    { name: '금융', percentage: 25, color: 'bg-emerald-500' },
    { name: '헬스케어', percentage: 20, color: 'bg-purple-500' },
    { name: '기타', percentage: 10, color: 'bg-gray-500' },
  ];

  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      return (
        <div className="bg-[#1a1a1a] border border-white/20 rounded-lg p-3 shadow-lg">
          <p className="text-white font-medium">{label}</p>
          <p className="text-emerald-400">자산: ₩{(payload[0].value / 1000000).toFixed(1)}M</p>
          <p className="text-blue-400">수익률: {payload[1]?.value?.toFixed(1)}%</p>
        </div>
      );
    }
    return null;
  };

  const handleNavigate = (key: string) => {
    switch (key) {
      case "dashboard":
        router.push("/dashboard"); break;
      case "portfolio":
        router.push("/portfolio"); break;
      case "signals":
        router.push("/autotrade"); break;
      case "chat":
        router.push("/chat"); break;
      case "settings":
        router.push("/settings"); break;
      default:
        break;
    }
  };

  return (
    <div className="min-h-screen w-full bg-gradient-to-br from-black via-gray-900 to-gray-820 text-white">
      <Header onSidebarOpen={() => setSidebarOpen(true)} />
      <AppSidebar 
        open={sidebarOpen} 
        onClose={() => setSidebarOpen(false)} 
        onNavigate={handleNavigate}
      />
      <main className="flex flex-col items-center px-6 md:px-12 py-8 bg-transparent">
        <h1 className="text-4xl md:text-6xl font-bold mb-8 tracking-tight text-white text-balance">
          Professional <span className="bg-gradient-to-r from-purple-400 to-blue-400 bg-clip-text text-transparent">Portfolio</span>
        </h1>
        
        {/* Charts Section */}
        <div className="w-full max-w-6xl mb-8">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* Performance Graph */}
            <div className="metric-card p-6">
              <div className="flex items-center gap-3 mb-6">
                <BarChart3 className="text-blue-400" size={24} />
                <h2 className="text-xl font-semibold text-white">포트폴리오 성과</h2>
              </div>
              
              {/* Real Chart */}
              <div className="h-64">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={performanceData}>
                    <defs>
                      <linearGradient id="colorValue" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#3B82F6" stopOpacity={0.8}/>
                        <stop offset="95%" stopColor="#3B82F6" stopOpacity={0.1}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#374151" />
                    <XAxis 
                      dataKey="month" 
                      stroke="#9CA3AF" 
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis 
                      stroke="#9CA3AF" 
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(value) => `₩${(value / 1000000).toFixed(0)}M`}
                    />
                    <Tooltip content={<CustomTooltip />} />
                    <Area 
                      type="monotone" 
                      dataKey="value" 
                      stroke="#3B82F6" 
                      strokeWidth={2}
                      fillOpacity={1} 
                      fill="url(#colorValue)" 
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
              
              <div className="mt-4 text-sm text-gray-400">
                최근 12개월 자산 가치 추이
              </div>
            </div>

            {/* Pie Chart */}
            <div className="metric-card p-6">
              <div className="flex items-center gap-3 mb-6">
                <PieChart className="text-purple-400" size={24} />
                <h2 className="text-xl font-semibold text-white">자산 분산</h2>
              </div>
              
              {/* Real Pie Chart */}
              <div className="h-64 flex items-center justify-center">
                <ResponsiveContainer width="100%" height="100%">
                  <RechartsPieChart>
                    <Pie
                      data={pieData}
                      cx="50%"
                      cy="50%"
                      innerRadius={60}
                      outerRadius={100}
                      paddingAngle={0}
                      dataKey="value"
                      stroke="none"
                    >
                      {pieData.map((entry, index) => (
                        <Cell key={`cell-${index}`} fill={entry.color} />
                      ))}
                    </Pie>
                    <Tooltip 
                      content={({ active, payload }) => {
                        if (active && payload && payload.length) {
                          return (
                            <div className="bg-[#1a1a1a] border border-white/20 rounded-lg p-3 shadow-lg">
                              <p className="text-white font-medium">{payload[0].name}</p>
                              <p className="text-emerald-400">{payload[0].value}%</p>
                            </div>
                          );
                        }
                        return null;
                      }}
                    />
                  </RechartsPieChart>
                </ResponsiveContainer>
                
                {/* Center content */}
                <div className="absolute text-center">
                  <div className="text-3xl font-bold text-white mb-2">8.2</div>
                  <div className="text-sm text-gray-400">다양성 지수</div>
                  <div className="text-xs text-emerald-400 font-medium mt-1">우수</div>
                </div>
              </div>
              
              {/* Professional Legend - Horizontal Layout */}
              <div className="flex items-center justify-between mt-6 px-2">
                {allocations.map((item, index) => (
                  <div key={index} className="flex items-center gap-2">
                    <div className={`w-3 h-3 ${item.color} rounded-full`}></div>
                    <div className="text-center">
                      <div className="text-sm font-medium text-white">{item.name}</div>
                      <div className="text-xs text-gray-400">{item.percentage}%</div>
                    </div>
                  </div>
                ))}
              </div>
            </div>
          </div>
        </div>

        {/* Stats Grid - Horizontal Layout */}
        <div className="w-full max-w-6xl mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {stats.map((stat, index) => (
              <div key={index} className="metric-card p-4">
                <div className="flex items-center justify-between mb-2">
                  <div className={`w-8 h-8 ${stat.color} rounded-lg flex items-center justify-center`}>
                    <stat.icon size={18} className="text-white" />
                  </div>
                  <span className="text-xs text-gray-300 bg-white/10 px-1.5 py-0.5 rounded-full">
                    {stat.percentage}
                  </span>
                </div>
                <div className="metric-label text-sm">{stat.title}</div>
                <div className="metric-value text-lg">{stat.value}</div>
                {stat.change && (
                  <div className="metric-change text-sm">{stat.change}</div>
                )}
                {stat.subtitle && (
                  <div className="text-sm text-gray-500">{stat.subtitle}</div>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Portfolio Details */}
        <div className="w-full max-w-6xl">
          <div className="metric-card p-6">
            <div className="flex items-center gap-3 mb-6">
              <History className="text-emerald-400" size={24} />
              <h2 className="text-xl font-semibold text-white">포트폴리오 상세</h2>
            </div>
            
            <div className="grid grid-cols-4 gap-4 mb-6">
              <button className="px-4 py-2 bg-white/20 rounded-lg text-sm text-white">개요</button>
              <button className="px-4 py-2 hover:bg-white/20 rounded-lg text-sm text-gray-400 transition-colors">보유 종목</button>
              <button className="px-4 py-2 hover:bg-white/20 rounded-lg text-sm text-gray-400 transition-colors">거래 내역</button>
              <button className="px-4 py-2 hover:bg-white/20 rounded-lg text-sm text-gray-400 transition-colors">성과 분석</button>
            </div>

            <div className="grid grid-cols-2 gap-8">
              {/* Monthly Returns */}
              <div>
                <h3 className="text-lg font-medium mb-4 text-white">월별 수익률</h3>
                <div className="space-y-3">
                  {monthlyReturns.map((item, index) => (
                    <div key={index} className="flex items-center justify-between py-2">
                      <span className="text-gray-300">{item.month}</span>
                      <span className={`font-medium ${item.positive ? 'text-emerald-400' : 'text-red-400'}`}>
                        {item.return}
                      </span>
                    </div>
                  ))}
                </div>
              </div>

              {/* Sector Allocation */}
              <div>
                <h3 className="text-lg font-medium mb-4 text-white">섹터별 분산</h3>
                <div className="space-y-3">
                  {allocations.map((item, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-gray-300">{item.name}</span>
                        <span className="font-medium text-white">{item.percentage}%</span>
                      </div>
                      <div className="w-full bg-white/20 rounded-full h-2">
                        <div 
                          className={`${item.color} h-2 rounded-full transition-all duration-500`}
                          style={{ width: `${item.percentage}%` }}
                        ></div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>
          </div>
        </div>
      </main>
    </div>
  );
}
