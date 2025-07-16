import React, { createContext, useContext, useState } from "react";

const SidebarContext = createContext<{
  open: boolean;
  setOpen: (open: boolean) => void;
} | null>(null);

export function SidebarProvider({ children, defaultOpen = false }: { children: React.ReactNode; defaultOpen?: boolean }) {
  const [open, setOpen] = useState(defaultOpen);
  return (
    <SidebarContext.Provider value={{ open, setOpen }}>
      {children}
    </SidebarContext.Provider>
  );
}

export function useSidebar() {
  const ctx = useContext(SidebarContext);
  if (!ctx) throw new Error("useSidebar must be used within a SidebarProvider");
  return ctx;
}

// Minimal stub components for AppSidebar compatibility
export function Sidebar({ children, className = '', ...props }: React.ComponentProps<"div">) {
  // Detect open state from context for animation
  const ctx = useContext(SidebarContext);
  const open = ctx ? ctx.open : false;
  return (
    <div
      className={`fixed top-0 left-0 z-50 min-h-screen h-screen w-64 bg-sidebar shadow-xl
        transition-transform transition-opacity transition-shadow
        duration-500
        [transition-timing-function:cubic-bezier(0.22,0.61,0.36,1)]
        overflow-y-auto scrollbar-hide
        ${open ? 'translate-x-0 scale-100 opacity-100 shadow-2xl' : '-translate-x-full scale-90 opacity-0 shadow-none'}
        ${className}`}
      style={{ willChange: 'transform, opacity, box-shadow' }}
      {...props}
    >
      {children}
    </div>
  );
}
export function SidebarContent({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}
export function SidebarFooter({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}
export function SidebarGroup({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}
export function SidebarGroupContent({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}
export function SidebarGroupLabel({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}
export function SidebarHeader({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
}
export function SidebarMenu({ children, ...props }: React.ComponentProps<"ul">) {
  return <ul {...props}>{children}</ul>;
}
export function SidebarMenuButton({ children, isActive, asChild, ...props }: React.ComponentProps<"button"> & { isActive?: boolean, asChild?: boolean }) {
  // Remove isActive/asChild from props to avoid React warning
  return <button {...props}>{children}</button>;
}
export function SidebarMenuItem({ children, ...props }: React.ComponentProps<"li">) {
  return <li {...props}>{children}</li>;
}
export function SidebarRail({ children, ...props }: React.ComponentProps<"div">) {
  return <div {...props}>{children}</div>;
} 