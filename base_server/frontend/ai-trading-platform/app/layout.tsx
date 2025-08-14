import type React from "react"
import type { Metadata } from "next"
import { Inter } from "next/font/google"
import "../styles/globals.css"
import { ThemeProvider } from "@/components/theme-provider"
import { Toaster } from "@/components/ui/toaster"
import { StoreProvider } from "@/providers/store-provider"
import { WebSocketProvider } from "@/providers/websocket-provider"
import { DynamicAuthProvider } from "@/providers/dynamic-auth-provider"
import { RouteProgressBar } from "@/components/layout/route-progress-bar"

const inter = Inter({ subsets: ["latin"] })

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

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="ko" suppressHydrationWarning data-scroll-behavior="smooth">
      <body className={inter.className}>
        <StoreProvider>
          <DynamicAuthProvider>
            <WebSocketProvider>
              <ThemeProvider
                attribute="class"
                defaultTheme="system"
                enableSystem
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