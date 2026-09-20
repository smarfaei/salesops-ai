"use client";

import { useCallback, useState } from "react";
import { Plus } from "lucide-react";
import { useAuth } from "@/components/auth-provider";
import { PageHeader } from "@/components/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Input, Label, Select } from "@/components/ui/form-controls";
import { ErrorState, LoadingState } from "@/components/ui/state";
import { useApi } from "@/hooks/use-api";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";
import { roleLabel } from "@/lib/permissions";
import type { UserRole } from "@/types";

const roles: UserRole[] = ["admin", "sales_manager", "sales_rep", "viewer"];

export default function UsersPage() {
  const { can } = useAuth();
  if (!can("user:manage")) {
    return <ErrorState message="Administrator access is required." />;
  }
  return <AuthorizedUsersPage />;
}

function AuthorizedUsersPage() {
  const loader = useCallback(() => api.users(), []);
  const { data, loading, error, reload } = useApi(loader);
  const [creating, setCreating] = useState(false);
  const [formError, setFormError] = useState<string | null>(null);

  const create = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    setFormError(null);
    try {
      await api.createUser({
        full_name: String(values.get("full_name")),
        email: String(values.get("email")),
        password: String(values.get("password")),
        role: String(values.get("role")) as UserRole,
      });
      setCreating(false);
      await reload();
    } catch (caught) {
      setFormError(
        caught instanceof Error ? caught.message : "Unable to create user",
      );
    }
  };

  return (
    <>
      <PageHeader
        title="Users"
        description="Manage access and sales responsibilities without exposing credentials."
        action={
          <Button onClick={() => setCreating((value) => !value)}>
            <Plus className="size-4" /> Create user
          </Button>
        }
      />
      {creating && (
        <form
          onSubmit={create}
          className="mb-5 rounded-xl border border-blue-100 bg-white p-5"
        >
          <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
            <div>
              <Label htmlFor="user-name">Full name</Label>
              <Input id="user-name" name="full_name" required />
            </div>
            <div>
              <Label htmlFor="user-email">Email</Label>
              <Input id="user-email" name="email" type="email" required />
            </div>
            <div>
              <Label htmlFor="user-password">Initial password</Label>
              <Input
                id="user-password"
                name="password"
                type="password"
                minLength={10}
                required
              />
            </div>
            <div>
              <Label htmlFor="user-role">Role</Label>
              <Select id="user-role" name="role" defaultValue="sales_rep">
                {roles.map((role) => (
                  <option key={role} value={role}>
                    {roleLabel[role]}
                  </option>
                ))}
              </Select>
            </div>
          </div>
          {formError && (
            <p role="alert" className="mt-3 text-sm text-rose-700">
              {formError}
            </p>
          )}
          <div className="mt-4 flex gap-2">
            <Button>Create user</Button>
            <Button
              type="button"
              variant="ghost"
              onClick={() => setCreating(false)}
            >
              Cancel
            </Button>
          </div>
        </form>
      )}
      {loading ? (
        <LoadingState label="Loading users" />
      ) : error ? (
        <ErrorState message={error} onRetry={reload} />
      ) : (
        <div className="overflow-x-auto rounded-xl border border-slate-200 bg-white">
          <table className="w-full min-w-[850px] text-left text-sm">
            <thead className="border-b border-slate-200 bg-slate-50 text-xs uppercase text-slate-500">
              <tr>
                <th className="p-4">User</th>
                <th className="p-4">Role</th>
                <th className="p-4">Status</th>
                <th className="p-4">Created</th>
                <th className="p-4">Controls</th>
              </tr>
            </thead>
            <tbody className="divide-y divide-slate-100">
              {data?.items.map((user) => (
                <tr key={user.id}>
                  <td className="p-4">
                    <p className="font-semibold">{user.full_name}</p>
                    <p className="text-xs text-slate-500">{user.email}</p>
                  </td>
                  <td className="p-4">
                    <Select
                      aria-label={`Role for ${user.full_name}`}
                      value={user.role}
                      onChange={(event) =>
                        void api
                          .updateUser(user.id, {
                            role: event.target.value as UserRole,
                          })
                          .then(reload)
                      }
                    >
                      {roles.map((role) => (
                        <option key={role} value={role}>
                          {roleLabel[role]}
                        </option>
                      ))}
                    </Select>
                  </td>
                  <td className="p-4">
                    <Badge
                      className={
                        user.is_active
                          ? "bg-emerald-50 text-emerald-700"
                          : "bg-slate-100 text-slate-600"
                      }
                    >
                      {user.is_active ? "Active" : "Inactive"}
                    </Badge>
                  </td>
                  <td className="p-4 text-xs text-slate-500">
                    {user.created_at ? formatDate(user.created_at) : "—"}
                  </td>
                  <td className="p-4">
                    <Button
                      size="sm"
                      variant="outline"
                      onClick={() =>
                        void api
                          .updateUser(user.id, { is_active: !user.is_active })
                          .then(reload)
                      }
                    >
                      {user.is_active ? "Deactivate" : "Activate"}
                    </Button>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </>
  );
}
