import type { HTMLAttributes } from "react";
import { cn } from "@/lib/utils";
export const Card = ({ className, ...p }: HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn(
      "rounded-xl border border-slate-200 bg-white shadow-sm",
      className,
    )}
    {...p}
  />
);
export const CardHeader = ({
  className,
  ...p
}: HTMLAttributes<HTMLDivElement>) => (
  <div
    className={cn("flex items-start justify-between gap-4 p-5 pb-2", className)}
    {...p}
  />
);
export const CardContent = ({
  className,
  ...p
}: HTMLAttributes<HTMLDivElement>) => (
  <div className={cn("p-5 pt-3", className)} {...p} />
);
