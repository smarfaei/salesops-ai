import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import LoginPage from "@/app/login/page";
import UsersPage from "@/app/users/page";

const mocks = vi.hoisted(() => ({
  login: vi.fn(),
  can: vi.fn(),
  users: vi.fn(),
  createUser: vi.fn(),
  updateUser: vi.fn(),
  reload: vi.fn(),
}));

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ login: mocks.login, can: mocks.can }),
}));
vi.mock("@/hooks/use-api", () => ({
  useApi: () => ({
    data: { items: [], total: 0, page: 1, page_size: 20, pages: 0 },
    loading: false,
    error: null,
    reload: mocks.reload,
  }),
}));
vi.mock("@/lib/api", () => ({
  api: {
    users: mocks.users,
    createUser: mocks.createUser,
    updateUser: mocks.updateUser,
  },
}));

describe("authentication and administration UI", () => {
  beforeEach(() => {
    vi.clearAllMocks();
    mocks.login.mockResolvedValue(undefined);
  });

  it("submits login credentials through the auth provider", async () => {
    render(<LoginPage />);
    fireEvent.change(screen.getByLabelText("Email"), {
      target: { value: "rep@salesops.demo" },
    });
    fireEvent.change(screen.getByLabelText("Password"), {
      target: { value: "demo-only" },
    });
    fireEvent.click(screen.getByRole("button", { name: "Sign in" }));
    await waitFor(() =>
      expect(mocks.login).toHaveBeenCalledWith(
        "rep@salesops.demo",
        "demo-only",
      ),
    );
  });

  it("rejects non-admin access to the Users page in the UI", () => {
    mocks.can.mockReturnValue(false);
    render(<UsersPage />);
    expect(
      screen.getByText("Administrator access is required."),
    ).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /create user/i }),
    ).not.toBeInTheDocument();
  });

  it("shows user controls to an administrator", () => {
    mocks.can.mockReturnValue(true);
    render(<UsersPage />);
    expect(
      screen.getByRole("button", { name: /create user/i }),
    ).toBeInTheDocument();
  });
});
