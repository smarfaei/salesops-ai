import type { UserRole } from "@/types";

export type Permission =
  | "lead:create"
  | "lead:edit"
  | "lead:assign"
  | "pipeline:write"
  | "activity:write"
  | "task:write"
  | "intelligence:write"
  | "user:manage"
  | "audit:read";

const rolePermissions: Record<UserRole, ReadonlySet<Permission>> = {
  admin: new Set([
    "lead:create",
    "lead:edit",
    "lead:assign",
    "pipeline:write",
    "activity:write",
    "task:write",
    "intelligence:write",
    "user:manage",
    "audit:read",
  ]),
  sales_manager: new Set([
    "lead:create",
    "lead:edit",
    "lead:assign",
    "pipeline:write",
    "activity:write",
    "task:write",
    "intelligence:write",
    "audit:read",
  ]),
  sales_rep: new Set([
    "lead:edit",
    "pipeline:write",
    "activity:write",
    "task:write",
    "intelligence:write",
  ]),
  viewer: new Set(),
};

export const hasPermission = (role: UserRole, permission: Permission) =>
  rolePermissions[role].has(permission);

export const roleLabel: Record<UserRole, string> = {
  admin: "Administrator",
  sales_manager: "Sales Manager",
  sales_rep: "Sales Representative",
  viewer: "Viewer",
};
