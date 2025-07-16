"use client"

import { Card, CardContent } from "@/components/ui/card"
import type { LucideIcon } from "lucide-react"

interface FeatureCardProps {
  icon: LucideIcon
  title: string
  description: string
  gradient: string
}

export function FeatureCard({ icon: Icon, title, description, gradient }: FeatureCardProps) {
  return (
    <Card className="group glass-card border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl hover:shadow-2xl transition-all duration-500 hover:scale-105">
      <CardContent className="p-8 text-center">
        <div className="space-y-6">
          <div
            className={`w-16 h-16 mx-auto rounded-2xl bg-gradient-to-br ${gradient} flex items-center justify-center shadow-lg group-hover:scale-110 transition-transform duration-300`}
          >
            <Icon className="h-8 w-8 text-white" />
          </div>

          <div className="space-y-3">
            <h3 className="text-xl font-bold text-gray-900 dark:text-white">{title}</h3>
            <p className="text-gray-600 dark:text-gray-300 leading-relaxed">{description}</p>
          </div>
        </div>
      </CardContent>
    </Card>
  )
}
