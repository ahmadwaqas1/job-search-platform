import { useState } from "react";
import { Navigate } from "react-router-dom";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { useLogin, useMe, useRegister } from "@/features/auth/api";
import { useAuthStore } from "@/store/authStore";

export function LoginPage() {
  const token = useAuthStore((s) => s.token);
  const { data: me, isLoading: meLoading } = useMe();
  const [mode, setMode] = useState<"login" | "register">("login");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const login = useLogin();
  const register = useRegister();

  if (token && (me || meLoading)) {
    if (me) return <Navigate to="/" replace />;
  }

  const mutation = mode === "login" ? login : register;

  return (
    <div className="flex min-h-screen items-center justify-center bg-muted/40 px-4">
      <Card className="w-full max-w-sm">
        <CardHeader>
          <CardTitle>Job Search Copilot</CardTitle>
          <CardDescription>
            {mode === "login"
              ? "Sign in to your self-hosted instance."
              : "Create the owner account. Only works once, on a fresh install."}
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form
            className="flex flex-col gap-3"
            onSubmit={(e) => {
              e.preventDefault();
              mutation.mutate({ email, password });
            }}
          >
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                autoComplete="username"
              />
            </div>
            <div className="flex flex-col gap-1.5">
              <Label htmlFor="password">Password</Label>
              <Input
                id="password"
                type="password"
                required
                minLength={8}
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                autoComplete={mode === "login" ? "current-password" : "new-password"}
              />
            </div>
            {mutation.isError && (
              <p className="text-sm text-destructive">
                {(mutation.error as { response?: { data?: { detail?: string } } })?.response?.data?.detail ??
                  "Something went wrong."}
              </p>
            )}
            <Button type="submit" disabled={mutation.isPending} className="mt-1">
              {mode === "login" ? "Sign in" : "Create owner account"}
            </Button>
          </form>
          <button
            className="mt-4 w-full text-center text-xs text-muted-foreground hover:text-foreground"
            onClick={() => setMode(mode === "login" ? "register" : "login")}
          >
            {mode === "login" ? "First time setting this up? Create the owner account" : "Already have an account? Sign in"}
          </button>
        </CardContent>
      </Card>
    </div>
  );
}
