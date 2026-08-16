import {
  Bot,
  Briefcase,
  FileUser,
  LayoutDashboard,
  LineChart,
  LogOut,
  Settings as SettingsIcon,
  Sparkles,
} from "lucide-react";
import { NavLink, Outlet } from "react-router-dom";

import { useMe } from "@/features/auth/api";
import { cn } from "@/lib/utils";
import { useAuthStore } from "@/store/authStore";

const NAV_ITEMS = [
  { to: "/", label: "Dashboard", icon: LayoutDashboard, end: true },
  { to: "/profile", label: "Profile & CV", icon: FileUser },
  { to: "/jobs", label: "Smart Match", icon: Sparkles },
  { to: "/applications", label: "Applications", icon: Briefcase },
  { to: "/market", label: "Market Insights", icon: LineChart },
  { to: "/copilot", label: "Copilot", icon: Bot },
  { to: "/settings", label: "Settings", icon: SettingsIcon },
];

export function AppLayout() {
  const { data: me } = useMe();
  const logout = useAuthStore((s) => s.logout);

  return (
    <div className="flex min-h-screen">
      <aside className="flex w-60 flex-shrink-0 flex-col border-r border-border bg-card">
        <div className="flex items-center gap-2 px-4 py-4">
          <Sparkles className="h-5 w-5 text-primary" />
          <span className="font-semibold">Job Search Copilot</span>
        </div>
        <nav className="flex flex-1 flex-col gap-0.5 px-2">
          {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
            <NavLink
              key={to}
              to={to}
              end={end}
              className={({ isActive }) =>
                cn(
                  "flex items-center gap-2.5 rounded-md px-3 py-2 text-sm font-medium transition-colors",
                  isActive ? "bg-primary/10 text-primary" : "text-muted-foreground hover:bg-accent hover:text-foreground"
                )
              }
            >
              <Icon className="h-4 w-4" />
              {label}
            </NavLink>
          ))}
        </nav>
        <div className="border-t border-border p-3">
          <div className="mb-2 truncate px-1 text-xs text-muted-foreground">{me?.email}</div>
          <button
            onClick={logout}
            className="flex w-full items-center gap-2 rounded-md px-3 py-2 text-sm text-muted-foreground hover:bg-accent hover:text-foreground"
          >
            <LogOut className="h-4 w-4" />
            Log out
          </button>
        </div>
      </aside>
      <main className="flex-1 overflow-y-auto">
        <div className="mx-auto max-w-6xl px-6 py-8">
          <Outlet />
        </div>
      </main>
    </div>
  );
}
