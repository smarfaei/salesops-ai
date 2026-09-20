import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LeadSummary } from "@/features/leads/lead-summary";
const lead = {
  id: 7,
  name: "Alex Rivera",
  company: "OrbitFlow SaaS",
  employees: 120,
  need: "AI sales qualification",
  budget: 8000,
  score: 100,
  status: "Hot" as const,
  score_reasons: [],
  pipeline_stage: "Qualified" as const,
  owner_user_id: null,
  owner: null,
  created_at: "2026-09-20T10:00:00Z",
  updated_at: "2026-09-20T10:00:00Z",
};
describe("Lead rendering", () => {
  it("shows real lead identity, company, score, status, and detail link", () => {
    render(<LeadSummary lead={lead} />);
    expect(screen.getByRole("link", { name: "Alex Rivera" })).toHaveAttribute(
      "href",
      "/leads/7",
    );
    expect(screen.getByText("AI sales qualification")).toBeInTheDocument();
  });
});
