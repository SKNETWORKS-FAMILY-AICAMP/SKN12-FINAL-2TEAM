"use client"

import { Avatar, AvatarFallback, AvatarImage } from "@/components/ui/avatar"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuLabel,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Badge } from "@/components/ui/badge"
import { User, Settings, LogOut, Crown, Shield } from "lucide-react"
import { useAuth } from "@/hooks/use-auth"
import { useRouter } from "next/navigation"

export function UserProfile() {
  const { logout } = useAuth();
  const router = useRouter();
  const handleLogout = async () => {
    await logout();
    router.push("/");
  };
  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button
          variant="ghost"
          className="w-full justify-start h-auto p-3 hover:bg-gray-100 dark:hover:bg-slate-700/50 rounded-xl"
        >
          <div className="flex items-center gap-3 w-full">
            <div className="relative">
              <Avatar className="h-10 w-10 ring-2 ring-blue-500/20">
                <AvatarImage src="/avatars/user.jpg" alt="User" />
                <AvatarFallback className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white font-semibold">
                  JD
                </AvatarFallback>
              </Avatar>
              <div className="absolute -bottom-1 -right-1 w-4 h-4 bg-green-500 rounded-full border-2 border-white dark:border-slate-800" />
            </div>
            <div className="flex-1 text-left">
              <div className="flex items-center gap-2">
                <p className="text-sm font-semibold text-gray-900 dark:text-white">John Doe</p>
                <Badge variant="outline" className="text-xs bg-yellow-50 text-yellow-700 border-yellow-200">
                  <Crown className="w-3 h-3 mr-1" />
                  Pro
                </Badge>
              </div>
              <p className="text-xs text-gray-500 dark:text-gray-400">Premium Member</p>
            </div>
          </div>
        </Button>
      </DropdownMenuTrigger>

      <DropdownMenuContent
        className="w-64 p-2 bg-white/95 dark:bg-slate-800/95 backdrop-blur-xl border-gray-200 dark:border-gray-700 shadow-xl"
        align="end"
      >
        <DropdownMenuLabel className="p-3">
          <div className="flex items-center gap-3">
            <Avatar className="h-12 w-12">
              <AvatarImage src="/avatars/user.jpg" alt="User" />
              <AvatarFallback className="bg-gradient-to-br from-blue-500 to-indigo-600 text-white">JD</AvatarFallback>
            </Avatar>
            <div>
              <p className="font-semibold text-gray-900 dark:text-white">John Doe</p>
              <p className="text-sm text-gray-500 dark:text-gray-400">john@example.com</p>
              <Badge variant="outline" className="text-xs mt-1 bg-green-50 text-green-700 border-green-200">
                <Shield className="w-3 h-3 mr-1" />
                인증됨
              </Badge>
            </div>
          </div>
        </DropdownMenuLabel>

        <DropdownMenuSeparator />

        <DropdownMenuItem className="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700">
          <User className="mr-3 h-4 w-4" />
          <span>프로필 관리</span>
        </DropdownMenuItem>

        <DropdownMenuItem className="p-3 rounded-lg hover:bg-gray-100 dark:hover:bg-slate-700">
          <Settings className="mr-3 h-4 w-4" />
          <span>계정 설정</span>
        </DropdownMenuItem>

        <DropdownMenuSeparator />

        <DropdownMenuItem
          className="p-3 rounded-lg hover:bg-red-50 dark:hover:bg-red-900/20 text-red-600 dark:text-red-400"
          onClick={handleLogout}
        >
          <LogOut className="mr-3 h-4 w-4" />
          <span>로그아웃</span>
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
