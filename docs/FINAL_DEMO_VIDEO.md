# SalesOps AI — Final 90-Second Demo Recording Plan

Record the public Railway deployment at 1600 × 900 or 1440 × 900. Use only the seeded fictional accounts and data. Hide bookmarks, notifications, developer tools, and the pointer whenever it is not demonstrating an action. Start with the Admin demo session ready and OrbitFlow SaaS unchanged from the seeded presentation state.

## Shot-by-shot plan

| Time | Exact action | On-screen caption | Optional voice-over |
| --- | --- | --- | --- |
| 0–6 sec | Begin on a clean title card, then reveal **Dashboard** without moving the pointer. | **SalesOps AI**<br>AI-Powered Lead Qualification & Sales Automation | “SalesOps AI turns inbound B2B leads into clear priorities and actionable follow-ups.” |
| 6–15 sec | Hold on the KPI row, then move once across **Total Leads**, **Hot Leads**, **Open Pipeline Value**, and the qualification/pipeline charts. | **Live sales operations overview** | “The live dashboard makes qualification, pipeline value, stage distribution, and follow-up workload visible at a glance.” |
| 15–23 sec | Click **Leads**. Pause on all six rows; point briefly to Score, Temperature, and Pipeline. | **Explainable qualification: Hot · Warm · Cold** | “Every lead receives a transparent score and a consistent Hot, Warm, or Cold classification.” |
| 23–35 sec | Click **Michael Brown**. Let the OrbitFlow SaaS detail page settle. Point to the 90/100 score, $9,000 budget, Qualified stage, owner, and activity timeline. | **One complete lead workspace** | “OrbitFlow brings the commercial context, ownership, tasks, and history into one record.” |
| 35–48 sec | In **Sales Intelligence**, move down the qualification summary, Buying signals, Risks to validate, and Next best action. Do not click Regenerate. | **Evidence-backed AI Sales Intelligence** | “The local intelligence provider uses known lead evidence to explain buying signals, surface risks, and recommend the next best action.” |
| 48–57 sec | Scroll just enough to reveal **Suggested follow-up**. Select **Copy** once only if the copy confirmation is visually clean. | **Personalized, human-reviewed follow-up** | “It also drafts a personalized follow-up while keeping the recommendation advisory and reviewable.” |
| 57–66 sec | Click **Create task**, enter `Confirm discovery agenda`, choose a near-future due date and Medium priority, then save. Immediately click its checkmark to complete it. | **Follow-up work stays visible** | “Tasks turn the recommendation into trackable sales work, from creation through completion.” |
| 66–75 sec | Click **Pipeline**. On a non-hero demo lead, change one stage by a single step and wait for the board to settle. | **Every stage change is recorded** | “The six-stage pipeline keeps opportunities moving and records every successful transition.” |
| 75–82 sec | Return to that lead and show the new stage-change timeline entry, then open **Audit** for the corresponding safe event view. | **Auditable activity and access history** | “Timeline and audit events preserve who changed what and when.” |
| 82–88 sec | Sign out. Hold on the login screen and its four public demo roles; do not enter the password on camera. | **Role-focused demo accounts** | “Admin, Manager, Sales Rep, and Viewer roles demonstrate centralized permissions and ownership.” |
| 88–90 sec | Cut to the closing card. | **SalesOps AI**<br>Live Demo · GitHub<br>frontend-production-9ca5.up.railway.app | “Explore the live demo and full source on GitHub.” |

## Recording notes

- Use one pointer path per shot; avoid circles, rapid movements, zoom effects, and repeated clicks.
- Wait for every loading state to disappear before continuing.
- Do not expose passwords, cookies, tokens, Railway variables, browser storage, or developer tools.
- The task and stage changes are safe demo interactions, but run the guarded Railway reset after recording so the public dataset returns to its canonical six-lead state.
- Record the UI first, then add the title/caption cards in editing. Keep transitions to 150–250 ms crossfades.
- Use a neutral soundtrack only if it remains below the narration and does not distract from product behavior.

## Final preflight

1. Reset with `python -m app.seed --reset --with-intelligence --with-users` in the Railway backend service.
2. Confirm six leads, OrbitFlow intelligence, the stage distribution, varied tasks, and a clean Audit Log.
3. Sign in as Admin, open Dashboard, and wait until all charts render.
4. Record a silent practice pass in under 90 seconds.
5. Capture the final pass, restore the demo dataset again, and verify the public Dashboard.
