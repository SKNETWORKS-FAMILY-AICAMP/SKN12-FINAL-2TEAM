"use client"

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { BarChart2, Zap, Trash2, Pause, Play, Plus } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import { AddStrategyModal } from "./add-strategy-modal";

interface Strategy {
  id: number;
  name: string;
  subtitle: string;
  philosophy: string;
  profit: string;
  profitColor: string;
  winRate: string;
  trades: number;
  recent: string;
  statusColor: string;
  isActive: boolean;
  stockInfo?: any;
}

export function StrategyGrid() {
  const [strategies, setStrategies] = useState<Strategy[]>([]);
  const [isModalOpen, setIsModalOpen] = useState(false);

  const addNewStrategy = (strategy: Strategy) => {
    setStrategies(prev => [...prev, strategy]);
  };

  const toggleStrategyStatus = (id: number) => {
    setStrategies(prev => 
      prev.map(strategy => 
        strategy.id === id 
          ? { ...strategy, isActive: !strategy.isActive }
          : strategy
      )
    );
  };

  const deleteStrategy = (id: number) => {
    setStrategies(prev => prev.filter(strategy => strategy.id !== id));
  };

  return (
    <div className="space-y-6">
      {/* Header with Add Button */}
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold">자동매매 시그널</h1>
          <p className="text-muted-foreground mt-2">
            AI가 당신이 선택한 기업의 자동매매 시그널을 알려줍니다
          </p>
        </div>

        <div className="flex gap-3">
          <Button 
            variant="outline"
            size="sm" 
            className="flex items-center gap-2 rounded-2xl shadow"
            onClick={() => setIsModalOpen(true)}
          >
            <Plus className="w-4 h-4" />
            새 시그널 추가하기
          </Button>
        </div>
      </div>

      {/* Empty State */}
      {strategies.length === 0 && (
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          className="text-center py-20"
        >
          <div className="w-24 h-24 mx-auto mb-6 rounded-full bg-[#0f172a]/50 flex items-center justify-center">
            <Zap className="w-12 h-12 text-muted-foreground" />
          </div>
          <h3 className="text-xl font-semibold mb-2">시그널이 없습니다</h3>
          <p className="text-muted-foreground mb-6">
            첫 번째 매매 시그널을 추가해보세요
          </p>
        </motion.div>
      )}

      {/* Strategies Grid */}
      <div className="grid gap-6 grid-cols-1 md:grid-cols-2">
        <AnimatePresence>
          {strategies.map((strategy, index) => (
            <motion.div
              key={strategy.id}
              initial={{ opacity: 0, y: 20, scale: 0.9 }}
              animate={{ opacity: 1, y: 0, scale: 1 }}
              exit={{ opacity: 0, y: -20, scale: 0.9 }}
              transition={{ 
                delay: index * 0.1,
                duration: 0.3,
                type: "spring",
                stiffness: 100
              }}
            >
              <Card className="rounded-2xl bg-[#0f172a]/70 backdrop-blur shadow-lg border border-white/10">
                <CardHeader className="pb-4 border-none">
                  <div className="flex items-start justify-between gap-3">
                    <div className="flex items-center gap-2">
                      <span className={`w-3 h-3 rounded-full ${strategy.statusColor}`}></span>
                      <div>
                        <CardTitle>{strategy.name}</CardTitle>
                        <CardDescription className="mt-1 text-sm text-muted-foreground">
                          {strategy.subtitle}
                        </CardDescription>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="rounded-full hover:bg-white/10"
                        onClick={() => toggleStrategyStatus(strategy.id)}
                      >
                        {strategy.isActive ? (
                          <Pause className="w-4 h-4" />
                        ) : (
                          <Play className="w-4 h-4" />
                        )}
                      </Button>
                      <Button 
                        variant="ghost" 
                        size="icon" 
                        className="rounded-full hover:bg-red-500/20 hover:text-red-400 transition-colors duration-200"
                        onClick={() => deleteStrategy(strategy.id)}
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </div>
                </CardHeader>

                <CardContent>
                  {/* 투자 철학 */}
                  <div className="rounded-lg bg-[#101827] p-4 text-sm text-muted-foreground">
                    <h3 className="font-medium mb-1 text-white">기업 설명</h3>
                    {strategy.philosophy}
                  </div>

                  {/* Stats */}
                  <div className="grid grid-cols-2 gap-4 text-center mt-6">
                    <div>
                      <p className={`text-2xl font-bold ${strategy.profitColor}`}>{strategy.profit}</p>
                      <p className="mt-1 text-sm text-muted-foreground">총 수익률</p>
                    </div>
                    <div>
                      <p className="text-2xl font-bold text-blue-400">{strategy.winRate}</p>
                      <p className="mt-1 text-sm text-muted-foreground">승률</p>
                    </div>
                  </div>

                  <div className="flex justify-between text-xs text-muted-foreground mt-6">
                    <span>총 시그널: {strategy.trades}회</span>
                    <span>최근 추가: {strategy.recent}</span>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          ))}
        </AnimatePresence>
      </div>
      {/* Add Strategy Modal */}
      <AddStrategyModal
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onAddStrategy={addNewStrategy}
      />
    </div>
  );
} 