import { describe, expect, it } from "vitest";
import { hasPermission, type Permission } from "@/lib/permissions";
import type { UserRole } from "@/types";

const permissions: Permission[] = [
  "lead:create",
  "lead:edit",
  "lead:assign",
  "pipeline:write",
  "activity:write",
  "task:write",
  "intelligence:write",
  "user:manage",
  "audit:read",
];

describe("role-aware UI permissions", () => {
  it("gives administrators every UI permission", () => {
    expect(
      permissions.every((permission) => hasPermission("admin", permission)),
    ).toBe(true);
  });

  it("lets managers run sales operations without user administration", () => {
    expect(hasPermission("sales_manager", "lead:assign")).toBe(true);
    expect(hasPermission("sales_manager", "audit:read")).toBe(true);
    expect(hasPermission("sales_manager", "user:manage")).toBe(false);
  });

  it("limits sales representatives to assigned-lead workflow actions", () => {
    expect(hasPermission("sales_rep", "lead:edit")).toBe(true);
    expect(hasPermission("sales_rep", "task:write")).toBe(true);
    expect(hasPermission("sales_rep", "lead:create")).toBe(false);
    expect(hasPermission("sales_rep", "lead:assign")).toBe(false);
    expect(hasPermission("sales_rep", "audit:read")).toBe(false);
  });

  it.each<UserRole>(["viewer"])("keeps %s read-only", (role) => {
    expect(
      permissions.some((permission) => hasPermission(role, permission)),
    ).toBe(false);
  });
});
