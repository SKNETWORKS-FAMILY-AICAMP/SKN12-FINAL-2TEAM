"use client";

// Simple event-based route progress controller
const START_EVENT = "route-progress-start";
const END_EVENT = "route-progress-end";

export function startRouteProgress(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(START_EVENT));
}

export function endRouteProgress(): void {
  if (typeof window === "undefined") return;
  window.dispatchEvent(new CustomEvent(END_EVENT));
}

export const ROUTE_PROGRESS_EVENTS = { START_EVENT, END_EVENT } as const;


