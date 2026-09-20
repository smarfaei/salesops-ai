"use client";

import { LockKeyhole, Sparkles } from "lucide-react";
import { useState } from "react";
import { useAuth } from "@/components/auth-provider";
import { Button } from "@/components/ui/button";
import { Input, Label } from "@/components/ui/form-controls";
import { DEMO_MODE } from "@/lib/config";

const demoAccounts = [
  ["Admin Demo", "admin@salesops.demo"],
  ["Sales Manager Demo", "manager@salesops.demo"],
  ["Sales Rep Demo", "rep@salesops.demo"],
  ["Viewer Demo", "viewer@salesops.demo"],
] as const;

export default function LoginPage() {
  const { login } = useAuth();
  const [email, setEmail] = useState(DEMO_MODE ? demoAccounts[2][1] : "");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const submit = async (event: React.FormEvent) => {
    event.preventDefault();
    setSubmitting(true);
    setError(null);
    try {
      await login(email, password);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Unable to sign in");
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <main className="grid min-h-screen bg-slate-950 lg:grid-cols-[1.1fr_0.9fr]">
      <section className="hidden flex-col justify-between p-12 text-white lg:flex">
        <div className="flex items-center gap-3">
          <div className="flex size-11 items-center justify-center rounded-xl bg-blue-600">
            <Sparkles className="size-5" />
          </div>
          <div>
            <p className="font-bold">SalesOps AI</p>
            <p className="text-xs text-slate-400">
              Secure sales automation workspace
            </p>
          </div>
        </div>
        <div className="max-w-xl">
          <p className="text-sm font-semibold uppercase tracking-[0.25em] text-blue-400">
            Production-style portfolio
          </p>
          <h1 className="mt-5 text-5xl font-bold leading-tight">
            The right sales view for every role.
          </h1>
          <p className="mt-5 text-lg leading-8 text-slate-300">
            Secure authentication, lead ownership, centralized permissions, and
            an auditable sales workflow.
          </p>
        </div>
        <p className="text-xs text-slate-500">
          AI-assisted recommendations remain human-reviewed.
        </p>
      </section>
      <section className="flex items-center justify-center bg-slate-50 p-5 sm:p-10">
        <div className="w-full max-w-md rounded-2xl border border-slate-200 bg-white p-7 shadow-xl shadow-slate-950/10 sm:p-9">
          <div className="flex size-11 items-center justify-center rounded-xl bg-blue-50 text-blue-700">
            <LockKeyhole className="size-5" />
          </div>
          <h2 className="mt-5 text-2xl font-bold text-slate-950">
            Sign in to SalesOps AI
          </h2>
          <p className="mt-2 text-sm text-slate-500">
            Access is controlled by your assigned sales role.
          </p>

          {DEMO_MODE && (
            <div className="mt-6 rounded-xl border border-blue-100 bg-blue-50/60 p-4">
              <p className="text-xs font-bold uppercase tracking-wide text-blue-800">
                Public demo accounts
              </p>
              <div className="mt-3 grid grid-cols-2 gap-2">
                {demoAccounts.map(([label, account]) => (
                  <button
                    key={account}
                    type="button"
                    onClick={() => setEmail(account)}
                    className="rounded-lg border border-blue-100 bg-white p-2 text-left text-xs hover:border-blue-300"
                  >
                    <span className="block font-semibold text-slate-800">
                      {label}
                    </span>
                    <span className="mt-1 block truncate text-slate-500">
                      {account}
                    </span>
                  </button>
                ))}
              </div>
              <p className="mt-3 text-xs text-blue-800">
                Select a role and use the demo-only password published with this
                deployment.
              </p>
            </div>
          )}

          <form onSubmit={submit} className="mt-6 space-y-4">
            <div>
              <Label htmlFor="login-email">Email</Label>
              <Input
                id="login-email"
                type="email"
                autoComplete="username"
                value={email}
                onChange={(event) => setEmail(event.target.value)}
                required
              />
            </div>
            <div>
              <Label htmlFor="login-password">Password</Label>
              <Input
                id="login-password"
                type="password"
                autoComplete="current-password"
                value={password}
                onChange={(event) => setPassword(event.target.value)}
                required
              />
            </div>
            {error && (
              <p
                role="alert"
                className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700"
              >
                {error}
              </p>
            )}
            <Button className="w-full" disabled={submitting}>
              {submitting ? "Signing in…" : "Sign in"}
            </Button>
          </form>
        </div>
      </section>
    </main>
  );
}
