"use client"

import type React from "react"
import { Provider } from "react-redux"
import { store } from "@/lib/store"

export function StoreProvider({ children }: { children: React.ReactNode }) {
  return <Provider store={store}>{children}</Provider>
}
