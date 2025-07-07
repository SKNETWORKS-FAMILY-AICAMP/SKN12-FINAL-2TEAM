"use client"

import { useState } from "react"
import { useRouter } from "next/navigation"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Label } from "@/components/ui/label"
import { Input } from "@/components/ui/input"
import { supabase } from "@/lib/supabaseClient"

export default function AccountCreation() {
  const router = useRouter()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [errorMsg, setErrorMsg] = useState("")

  const handleCreateAccount = async () => {
    setErrorMsg("")
    const { data, error } = await supabase.auth.signUp({
      email,
      password,
    })
    if (error) {
      setErrorMsg(error.message)
      return
    }
    // 회원가입 성공 시 이메일 인증 안내 페이지로 이동
    router.push("/email-verification")
  }

  return (
    <div className="flex flex-col items-center justify-center h-screen bg-gray-100">
      <Card className="w-full max-w-md">
        <CardHeader>
          <CardTitle>Create an Account</CardTitle>
        </CardHeader>
        <CardContent className="flex flex-col items-center justify-center gap-4 p-4">
          <div className="w-full">
            <Label htmlFor="email">Email</Label>
            <Input
              type="email"
              id="email"
              className="w-full h-10 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
            />
          </div>
          <div className="w-full">
            <Label htmlFor="password">Password</Label>
            <Input
              type="password"
              id="password"
              className="w-full h-10 px-3 py-2 border rounded-md focus:outline-none focus:ring-2 focus:ring-blue-500"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
            />
          </div>
          {errorMsg && (
            <div className="text-red-500 text-sm w-full text-center mb-2">{errorMsg}</div>
          )}
          <Button variant="primary" size="lg" onClick={handleCreateAccount}>
            Create Account
          </Button>
        </CardContent>
      </Card>
    </div>
  )
}
