import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { AuthProvider, useAuth } from "@/components/auth-provider";

const apiMocks = vi.hoisted(() => ({
  login: vi.fn(),
  logout: vi.fn(),
  refresh: vi.fn(),
  setAccessToken: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  api: {
    login: apiMocks.login,
    logout: apiMocks.logout,
    refresh: apiMocks.refresh,
  },
  setAccessToken: apiMocks.setAccessToken,
}));

const user = {
  id: 4,
  email: "viewer@salesops.demo",
  full_name: "Vera Viewer",
  role: "viewer" as const,
  is_active: true,
  created_at: "2026-09-20T10:00:00Z",
  updated_at: "2026-09-20T10:00:00Z",
  last_login_at: null,
};

function Probe() {
  const auth = useAuth();
  return (
    <div>
      <span>
        {auth.loading ? "loading" : (auth.user?.email ?? "anonymous")}
      </span>
      <span>{auth.can("lead:edit") ? "can-edit" : "read-only"}</span>
      <button onClick={() => void auth.login(user.email, "demo-password")}>
        login
      </button>
      <button onClick={() => void auth.logout()}>logout</button>
    </div>
  );
}

describe("AuthProvider", () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it("restores the current user from the refresh-token session without local storage", async () => {
    apiMocks.refresh.mockResolvedValue({
      access_token: "short-lived",
      token_type: "bearer",
      user,
    });
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    expect(screen.getByText("loading")).toBeInTheDocument();
    expect(await screen.findByText(user.email)).toBeInTheDocument();
    expect(screen.getByText("read-only")).toBeInTheDocument();
    expect(window.localStorage.length).toBe(0);
  });

  it("supports login and logout state transitions", async () => {
    apiMocks.refresh.mockRejectedValue(new Error("no session"));
    apiMocks.login.mockResolvedValue({
      access_token: "short-lived",
      token_type: "bearer",
      user,
    });
    apiMocks.logout.mockResolvedValue(undefined);
    render(
      <AuthProvider>
        <Probe />
      </AuthProvider>,
    );
    expect(await screen.findByText("anonymous")).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "login" }));
    expect(await screen.findByText(user.email)).toBeInTheDocument();

    fireEvent.click(screen.getByRole("button", { name: "logout" }));
    await waitFor(() =>
      expect(screen.getByText("anonymous")).toBeInTheDocument(),
    );
    expect(apiMocks.logout).toHaveBeenCalledOnce();
  });
});
