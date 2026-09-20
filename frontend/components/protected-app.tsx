"use client";

import { useEffect } from "react";
import { usePathname, useRouter } from "next/navigation";
import { AppShell } from "@/components/app-shell";
import { useAuth } from "@/components/auth-provider";

export function ProtectedApp({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  const router = useRouter();
  const { user, loading } = useAuth();
  const isLogin = path === "/login";

  useEffect(() => {
    if (!loading && !user && !isLogin) router.replace("/login");
    if (!loading && user && isLogin) router.replace("/");
  }, [isLogin, loading, router, user]);

  if (isLogin) return <>{children}</>;
  if (loading || !user) {
    return (
      <div className="flex min-h-screen items-center justify-center bg-slate-950 text-sm text-slate-300">
        Verifying secure session…
      </div>
    );
  }
  return <AppShell>{children}</AppShell>;
}
