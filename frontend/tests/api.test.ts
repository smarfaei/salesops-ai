import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";

describe("API client", () => {
  afterEach(() => vi.restoreAllMocks());
  it("builds backend lead filters and returns JSON", async () => {
    const mock = vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          items: [],
          total: 0,
          page: 1,
          page_size: 10,
          pages: 0,
        }),
        { status: 200, headers: { "Content-Type": "application/json" } },
      ),
    );
    await api.leads({ search: "Orbit", pipeline_stage: "Qualified", page: 2 });
    expect(mock).toHaveBeenCalledWith(
      expect.stringContaining(
        "/leads?search=Orbit&pipeline_stage=Qualified&page=2",
      ),
      expect.any(Object),
    );
  });
  it("surfaces FastAPI detail messages", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(JSON.stringify({ detail: "Lead not found" }), {
        status: 404,
        headers: { "Content-Type": "application/json" },
      }),
    );
    await expect(api.lead(999)).rejects.toMatchObject({
      message: "Lead not found",
      status: 404,
    });
  });
  it("surfaces structured public-demo restriction messages", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValue(
      new Response(
        JSON.stringify({
          error: {
            code: "http_error",
            message: "This operation is disabled in the public demo",
          },
        }),
        { status: 403, headers: { "Content-Type": "application/json" } },
      ),
    );
    await expect(api.createLead({} as never)).rejects.toMatchObject({
      message: "This operation is disabled in the public demo",
      status: 403,
    });
  });
});
