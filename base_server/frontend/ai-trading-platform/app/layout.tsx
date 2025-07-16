import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "../styles/globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/toaster"
import { AuthProvider } from "@/providers/auth-provider"
import { StoreProvider } from "@/providers/store-provider"
import { WebSocketProvider } from "@/providers/websocket-provider"

const inter = Inter({ subsets: ["latin"] })

export const metadata: Metadata = {
  title: "AI Trading Advisor - Smart Financial Decisions",
  description: "Advanced AI-powered trading platform with real-time market analysis",
    generator: 'v0.dev'
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body className={inter.className}>
        <StoreProvider>
          <AuthProvider>
            <WebSocketProvider>
              <ThemeProvider attribute="class" defaultTheme="system" enableSystem disableTransitionOnChange>
                {children}
                <Toaster />
              </ThemeProvider>
            </WebSocketProvider>
          </AuthProvider>
        </StoreProvider>
      </body>
    </html>
  )
}
