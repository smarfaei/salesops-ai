import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";
import { IntelligencePanel } from "@/features/intelligence/intelligence-panel";

vi.mock("@/components/auth-provider", () => ({
  useAuth: () => ({ can: () => true }),
}));

describe("Intelligence rendering", () => {
  it("labels AI advice and renders signals, action, and follow-up", async () => {
    vi.spyOn(api, "intelligence").mockResolvedValue({
      id: 1,
      lead_id: 7,
      qualification_summary: "Strong fit with confirmed budget.",
      buying_signals: [
        { signal: "High intent", evidence: "Requested AI automation" },
      ],
      risks: [{ signal: "Timeline", evidence: "Not confirmed" }],
      next_best_action: {
        action: "Book discovery",
        reason: "Validate timeline",
        priority: "high",
      },
      follow_up: {
        subject: "Next steps",
        message: "Let us schedule a focused discovery call.",
      },
      generated_at: "2026-09-20T10:00:00Z",
      provider: "local",
      model: null,
      provider_metadata: null,
    });
    render(<IntelligencePanel leadId={7} />);
    expect(
      await screen.findByText("Strong fit with confirmed budget."),
    ).toBeInTheDocument();
    expect(screen.getByText("AI-assisted recommendation")).toBeInTheDocument();
    expect(screen.getByText("High intent")).toBeInTheDocument();
    expect(screen.getByText("Book discovery")).toBeInTheDocument();
    expect(screen.getByText("Next steps")).toBeInTheDocument();
  });
});
