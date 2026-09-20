"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  BarChart3,
  BriefcaseBusiness,
  CheckSquare2,
  LayoutDashboard,
  Search,
  Sparkles,
  Users,
} from "lucide-react";
import { cn } from "@/lib/utils";
const nav = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/pipeline", label: "Pipeline", icon: BriefcaseBusiness },
  { href: "/tasks", label: "Tasks", icon: CheckSquare2 },
  { href: "/analytics", label: "Analytics", icon: BarChart3 },
];
export function AppShell({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  return (
    <div className="min-h-screen bg-slate-50">
      <aside className="fixed inset-y-0 left-0 z-30 hidden w-64 border-r border-slate-200 bg-slate-950 lg:block">
        <div className="flex h-20 items-center gap-3 px-6 text-white">
          <div className="flex size-10 items-center justify-center rounded-xl bg-blue-600">
            <Sparkles className="size-5" />
          </div>
          <div>
            <div className="font-bold">SalesOps AI</div>
            <div className="text-[11px] text-slate-400">
              Sales automation workspace
            </div>
          </div>
        </div>
        <nav className="space-y-1 px-3">
          {nav.map(({ href, label, icon: Icon }) => {
            const active = href === "/" ? path === href : path.startsWith(href);
            return (
              <Link
                key={href}
                href={href}
                className={cn(
                  "flex items-center gap-3 rounded-lg px-3 py-2.5 text-sm font-medium",
                  active
                    ? "bg-white/10 text-white"
                    : "text-slate-400 hover:bg-white/5 hover:text-white",
                )}
              >
                <Icon className="size-4" />
                {label}
              </Link>
            );
          })}
        </nav>
        <div className="absolute bottom-5 left-4 right-4 rounded-xl border border-white/10 bg-white/5 p-4">
          <p className="text-xs font-semibold text-white">
            AI-assisted decisions
          </p>
          <p className="mt-1 text-xs leading-5 text-slate-400">
            Recommendations support your sales team; people make the final call.
          </p>
        </div>
      </aside>
      <div className="lg:pl-64">
        <header className="sticky top-0 z-20 flex h-16 items-center justify-between border-b border-slate-200 bg-white/90 px-4 backdrop-blur sm:px-6 lg:px-8">
          <div className="hidden items-center gap-2 rounded-lg bg-slate-100 px-3 py-2 text-sm text-slate-400 sm:flex">
            <Search className="size-4" />
            Search leads from the Leads page
          </div>
          <div className="ml-auto flex items-center gap-3">
            <div className="hidden text-right sm:block">
              <p className="text-sm font-semibold text-slate-800">
                Portfolio Demo
              </p>
              <p className="text-xs text-slate-500">Sales operations</p>
            </div>
            <div className="flex size-9 items-center justify-center rounded-full bg-slate-900 text-xs font-bold text-white">
              SO
            </div>
          </div>
        </header>
        <nav className="flex overflow-x-auto border-b border-slate-200 bg-white px-2 py-2 lg:hidden">
          {nav.map(({ href, label, icon: Icon }) => (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex min-w-20 flex-col items-center gap-1 rounded-lg px-3 py-2 text-xs",
                (href === "/" ? path === href : path.startsWith(href))
                  ? "bg-blue-50 text-blue-700"
                  : "text-slate-500",
              )}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          ))}
        </nav>
        <main className="mx-auto max-w-[1600px] p-4 sm:p-6 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}
