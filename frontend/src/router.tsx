import { createBrowserRouter, Navigate } from "react-router-dom";

import { useMe } from "@/features/auth/api";
import { AppLayout } from "@/layouts/AppLayout";
import { ApplicationDetailPage } from "@/pages/ApplicationDetail";
import { ApplicationsPage } from "@/pages/Applications";
import { CopilotPage } from "@/pages/Copilot";
import { DashboardPage } from "@/pages/Dashboard";
import { JobDetailPage } from "@/pages/JobDetail";
import { JobsPage } from "@/pages/Jobs";
import { LoginPage } from "@/pages/Login";
import { MarketPage } from "@/pages/Market";
import { ProfilePage } from "@/pages/Profile";
import { SettingsPage } from "@/pages/Settings";
import { useAuthStore } from "@/store/authStore";

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const token = useAuthStore((s) => s.token);
  const { data: me, isLoading, isError } = useMe();

  if (!token) return <Navigate to="/login" replace />;
  if (isLoading) return <div className="p-8 text-muted-foreground">Loading...</div>;
  if (isError || !me) return <Navigate to="/login" replace />;
  return <>{children}</>;
}

export const router = createBrowserRouter([
  { path: "/login", element: <LoginPage /> },
  {
    path: "/",
    element: (
      <ProtectedRoute>
        <AppLayout />
      </ProtectedRoute>
    ),
    children: [
      { index: true, element: <DashboardPage /> },
      { path: "profile", element: <ProfilePage /> },
      { path: "jobs", element: <JobsPage /> },
      { path: "jobs/:id", element: <JobDetailPage /> },
      { path: "applications", element: <ApplicationsPage /> },
      { path: "applications/:id", element: <ApplicationDetailPage /> },
      { path: "market", element: <MarketPage /> },
      { path: "copilot", element: <CopilotPage /> },
      { path: "settings", element: <SettingsPage /> },
    ],
  },
]);
