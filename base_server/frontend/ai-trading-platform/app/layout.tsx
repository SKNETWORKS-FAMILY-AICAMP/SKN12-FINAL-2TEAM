import type React from "react"
import type { Metadata } from "next"
import { Noto_Sans_KR } from "next/font/google"
import "../styles/globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/toaster"
import { StoreProvider } from "@/providers/store-provider"
import { WebSocketProvider } from "@/providers/websocket-provider"
import { DynamicAuthProvider } from "@/providers/dynamic-auth-provider"
import { RouteProgressBar } from "@/components/layout/route-progress-bar"
import { cn } from "@/lib/utils"

const notoSans = Noto_Sans_KR({
  subsets: ["latin"],
  display: "swap",
  variable: "--font-sans",
})

export const metadata: Metadata = {
  title: "AI Trading Advisor",
  description: "AI-powered trading platform",
  icons: {
    icon: "/favicon.ico",
    apple: [
      { url: "/apple-touch-icon.png", sizes: "180x180", type: "image/png" },
      { url: "/apple-touch-icon-precomposed.png", sizes: "180x180", type: "image/png" }
    ]
  }
}

// Fast Refresh를 위한 명시적 컴포넌트 정의
function RootLayout({ children }: { children: React.ReactNode }) {
  return (
    <html lang="ko" suppressHydrationWarning>
      <body
        className={cn(
          "min-h-screen bg-background font-sans antialiased",
          notoSans.variable
        )}
      >
        <StoreProvider>
          <DynamicAuthProvider>
            <WebSocketProvider>
              <ThemeProvider
                attribute="class"
                defaultTheme="dark"
                enableSystem={false}
                disableTransitionOnChange
              >
                <RouteProgressBar />
                {children}
                <Toaster />
              </ThemeProvider>
            </WebSocketProvider>
          </DynamicAuthProvider>
        </StoreProvider>
      </body>
    </html>
  )
}

export default RootLayout 