"use client"

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Button } from "@/components/ui/button"
import { Badge } from "@/components/ui/badge"
import { Switch } from "@/components/ui/switch"
import { TrendingUp, Search, Target, Zap, Settings } from "lucide-react"
import { useChat } from "@/hooks/use-chat"

const toolIcons = {
  TrendingUp,
  Search,
  Target,
  Zap,
}

interface AIToolsPanelProps {
  selectedTool: string | null
  onToolSelect: (toolId: string | null) => void
}

export function AIToolsPanel({ selectedTool, onToolSelect }: AIToolsPanelProps) {
  const { availableTools } = useChat()

  return (
    <Card className="h-full border-0 bg-white/80 dark:bg-slate-800/80 backdrop-blur-xl professional-shadow">
      <CardHeader className="pb-4">
        <CardTitle className="flex items-center gap-2 text-lg">
          <Settings className="h-5 w-5" />
          AI 도구
        </CardTitle>
      </CardHeader>

      <CardContent className="space-y-4">
        {availableTools.map((tool) => {
          const IconComponent = toolIcons[tool.icon as keyof typeof toolIcons] || TrendingUp
          const isSelected = selectedTool === tool.id

          return (
            <div
              key={tool.id}
              className={`p-4 rounded-xl border transition-all duration-200 cursor-pointer ${
                isSelected
                  ? "bg-gradient-to-br from-blue-50 to-indigo-50 dark:from-blue-900/20 dark:to-indigo-900/20 border-blue-200 dark:border-blue-700"
                  : "bg-gray-50 dark:bg-slate-700/50 border-gray-200 dark:border-gray-600 hover:bg-gray-100 dark:hover:bg-slate-700"
              }`}
              onClick={() => onToolSelect(isSelected ? null : tool.id)}
            >
              <div className="flex items-start gap-3">
                <div
                  className={`p-2 rounded-lg ${
                    isSelected
                      ? "bg-gradient-to-br from-blue-500 to-indigo-600 text-white"
                      : "bg-gray-200 dark:bg-slate-600 text-gray-600 dark:text-gray-400"
                  }`}
                >
                  <IconComponent className="h-4 w-4" />
                </div>

                <div className="flex-1">
                  <div className="flex items-center justify-between mb-2">
                    <h3 className="font-medium text-sm">{tool.name}</h3>
                    <Switch checked={tool.isActive} />
                  </div>

                  <p className="text-xs text-gray-600 dark:text-gray-400 mb-3">{tool.description}</p>

                  <div className="flex items-center justify-between">
                    <Badge variant="outline" className="text-xs">
                      {tool.category}
                    </Badge>
                    {isSelected && (
                      <Badge variant="default" className="text-xs bg-blue-500">
                        활성화됨
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            </div>
          )
        })}

        <div className="pt-4 border-t border-gray-200 dark:border-gray-700">
          <Button variant="outline" className="w-full text-sm bg-transparent">
            도구 설정 관리
          </Button>
        </div>
      </CardContent>
    </Card>
  )
}
