import { describe, expect, it } from "vitest";
import {
  formatCurrency,
  isOverdue,
  stageTone,
  statusTone,
  stages,
} from "@/lib/utils";
describe("sales UI mappings", () => {
  it("defines every authoritative pipeline stage", () =>
    expect(stages).toEqual([
      "New",
      "Qualified",
      "Contacted",
      "Proposal",
      "Won",
      "Lost",
    ]));
  it("maps every qualification and stage to a visible tone", () => {
    expect(Object.keys(statusTone)).toEqual(["Hot", "Warm", "Cold"]);
    expect(Object.keys(stageTone)).toEqual(stages);
  });
  it("formats money and overdue state", () => {
    expect(formatCurrency(8000)).toContain("8,000");
    expect(isOverdue("2020-01-01T00:00:00Z", "pending")).toBe(true);
    expect(isOverdue("2020-01-01T00:00:00Z", "completed")).toBe(false);
  });
});
