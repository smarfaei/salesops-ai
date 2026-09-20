import { render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ProtectedApp } from "@/components/protected-app";

const mocks = vi.hoisted(() => ({
  replace: vi.fn(),
  pathname: "/leads",
  auth: { user: null as null | { id: number }, loading: false },
}));

vi.mock("next/navigation", () => ({
  usePathname: () => mocks.pathname,
  useRouter: () => ({ replace: mocks.replace }),
}));
vi.mock("@/components/auth-provider", () => ({ useAuth: () => mocks.auth }));
vi.mock("@/components/app-shell", () => ({
  AppShell: ({ children }: { children: React.ReactNode }) => (
    <div data-testid="shell">{children}</div>
  ),
}));

describe("ProtectedApp", () => {
  beforeEach(() => {
    mocks.replace.mockReset();
    mocks.pathname = "/leads";
    mocks.auth = { user: null, loading: false };
  });

  it("does not render protected content before authentication", async () => {
    render(
      <ProtectedApp>
        <div>private leads</div>
      </ProtectedApp>,
    );
    expect(screen.queryByText("private leads")).not.toBeInTheDocument();
    await waitFor(() => expect(mocks.replace).toHaveBeenCalledWith("/login"));
  });

  it("renders authenticated content inside the application shell", () => {
    mocks.auth = { user: { id: 1 }, loading: false };
    render(
      <ProtectedApp>
        <div>private leads</div>
      </ProtectedApp>,
    );
    expect(screen.getByTestId("shell")).toContainElement(
      screen.getByText("private leads"),
    );
  });

  it("keeps the login page public", () => {
    mocks.pathname = "/login";
    render(
      <ProtectedApp>
        <div>login form</div>
      </ProtectedApp>,
    );
    expect(screen.getByText("login form")).toBeInTheDocument();
  });
});
