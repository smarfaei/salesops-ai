"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { api } from "@/lib/api";
import type { Lead, LeadInput } from "@/types";
import { Button } from "@/components/ui/button";
import { Card, CardContent } from "@/components/ui/card";
import { Input, Label, Textarea } from "@/components/ui/form-controls";
const empty: LeadInput = {
  name: "",
  company: "",
  employees: 0,
  need: "",
  budget: 0,
};
export function LeadForm({ lead }: { lead?: Lead }) {
  const router = useRouter();
  const [form, setForm] = useState<LeadInput>(
    lead
      ? {
          name: lead.name,
          company: lead.company,
          employees: lead.employees,
          need: lead.need,
          budget: lead.budget,
        }
      : empty,
  );
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);
  const set = <K extends keyof LeadInput>(key: K, value: LeadInput[K]) =>
    setForm((x) => ({ ...x, [key]: value }));
  const submit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (!form.name.trim() || !form.company.trim() || !form.need.trim()) {
      setError("Name, company, and need are required.");
      return;
    }
    if (form.employees < 0 || form.budget < 0) {
      setError("Employees and budget cannot be negative.");
      return;
    }
    setSaving(true);
    try {
      const saved = lead
        ? await api.updateLead(lead.id, form)
        : await api.createLead(form);
      router.push(`/leads/${saved.id}`);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Unable to save lead");
    } finally {
      setSaving(false);
    }
  };
  return (
    <Card className="max-w-3xl">
      <CardContent className="pt-6">
        <form onSubmit={submit} className="space-y-5">
          <div className="grid gap-5 sm:grid-cols-2">
            <div>
              <Label htmlFor="lead-name">Contact name</Label>
              <Input
                id="lead-name"
                maxLength={100}
                value={form.name}
                onChange={(e) => set("name", e.target.value)}
                placeholder="Alex Morgan"
              />
            </div>
            <div>
              <Label htmlFor="lead-company">Company</Label>
              <Input
                id="lead-company"
                maxLength={100}
                value={form.company}
                onChange={(e) => set("company", e.target.value)}
                placeholder="OrbitFlow SaaS"
              />
            </div>
            <div>
              <Label htmlFor="lead-employees">Company size</Label>
              <Input
                id="lead-employees"
                type="number"
                min="0"
                value={form.employees}
                onChange={(e) => set("employees", Number(e.target.value))}
              />
            </div>
            <div>
              <Label htmlFor="lead-budget">Budget (USD)</Label>
              <Input
                id="lead-budget"
                type="number"
                min="0"
                value={form.budget}
                onChange={(e) => set("budget", Number(e.target.value))}
              />
            </div>
          </div>
          <div>
            <Label htmlFor="lead-need">Sales need</Label>
            <Textarea
              id="lead-need"
              maxLength={500}
              value={form.need}
              onChange={(e) => set("need", e.target.value)}
              placeholder="Describe the customer problem, urgency, and desired outcome."
            />
            <p className="mt-1 text-xs text-slate-400">
              The backend uses need, budget, and company size to calculate an
              explainable score.
            </p>
          </div>
          {error && (
            <p
              role="alert"
              className="rounded-lg bg-rose-50 p-3 text-sm text-rose-700"
            >
              {error}
            </p>
          )}
          <div className="flex gap-3">
            <Button disabled={saving}>
              {saving
                ? "Saving…"
                : lead
                  ? "Save changes"
                  : "Create and qualify lead"}
            </Button>
            <Button
              type="button"
              variant="outline"
              onClick={() => router.back()}
            >
              Cancel
            </Button>
          </div>
        </form>
      </CardContent>
    </Card>
  );
}
