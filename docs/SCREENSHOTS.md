# Portfolio Screenshot Plan

## Preparation

1. Use the dedicated Railway public-demo database.
2. Run `cd backend && python -m app.seed --reset --with-intelligence --with-users` in the backend service.
3. Start the full stack and use a 1440×1000 or larger desktop viewport.
4. Keep browser zoom at 100%, hide bookmarks/personal tabs, and capture only the application.
5. Confirm Dashboard shows exactly six fictional demo leads before capturing.

Do not add fake logos, fabricated metrics, or customer claims.

## `01-dashboard.png`

- Route: `/`
- Show all six KPI cards: 6 Total Leads, 3 Hot Leads, 1 Qualified Lead, open pipeline value, 1 Won Lead, and the current seeded Pending Tasks total.
- Include Lead Qualification and Pipeline Distribution charts; keep the lower chart row partially visible if needed.
- Capture the desktop sidebar and SalesOps AI brand.

## `02-leads.png`

- Route: `/leads`
- Clear all filters and sort by score descending if the strongest leads are not near the top.
- Show OrbitFlow SaaS, Cartloom Commerce, and the Hot/Warm/Cold badge variety.
- Include the search and filter controls plus table headings.

## `03-lead-detail.png`

- Route: OrbitFlow SaaS lead detail.
- Show Michael Brown, OrbitFlow SaaS, 90/100 Hot, Qualified, $9,000 budget, and the Lead Information panel.
- Include Intelligence, Tasks, and at least part of the Activity Timeline to communicate the CRM record structure.

## `04-ai-intelligence.png`

- Route: OrbitFlow SaaS lead detail.
- Frame the full Sales Intelligence card.
- Include the AI-assisted recommendation badge, qualification summary, buying signals, risks, next best action, and suggested follow-up.
- Ensure provider and generated time are visible.

## `05-pipeline.png`

- Route: `/pipeline`
- Capture all six columns with one seeded lead in each stage.
- Keep lead name, company, score, qualification badge, budget, and stage selector readable.
- Use a wide viewport; do not crop the Won or Lost columns.

## `06-tasks.png`

- Route: `/tasks`
- Use the Pending view and show the overdue Stonebridge task plus upcoming work.
- Include task title, lead, priority, due time, status, and action buttons.
- Capture the filter row so the operational workflow is obvious.

## `07-login-rbac.png`

- Sign out only after every authenticated screenshot is complete.
- Show the four public fictional role accounts and the complete sign-in card.
- Keep the password field empty and never expose the demo password in the image.

## `08-audit-log.png`

- Capture as Admin after the seeded dataset has produced a few meaningful safe events.
- Show successful login, task creation, intelligence generation, and activity creation.
- Exclude QA/test junk, secrets, request headers, and internal metadata.

## Final Review

- Use consistent dimensions and file naming.
- Check that no API keys, local paths, browser profiles, or personal notifications appear.
- Prefer PNG for crisp UI text.
- Save the final set under `docs/assets/` using the exact numbered names above.
- Re-run the demo reset after any screenshot interaction that changes stages or tasks.
