# SalesOps AI — Hero Asset Production Specification

## Source

Use only the clean, real public-demo Dashboard capture:

`docs/assets/01-dashboard.png`

Do not redraw, replace, or invent the dashboard. Preserve its real six-lead dataset and visible metrics. The screenshot should remain the dominant visual evidence, not a small decorative thumbnail.

## Required copy

**Title**
SalesOps AI

**Subtitle**
AI-Powered Lead Qualification & Sales Automation

**Supporting line**
Explainable Lead Scoring • AI Sales Intelligence • Pipeline Automation

## Art direction

- Premium B2B SaaS presentation in graphite, midnight navy, soft white, and restrained product-blue accents.
- Clean editorial hierarchy; modern, quiet, and credible.
- No neon gradients, glowing brains, robots, circuit patterns, fake customer logos, fake testimonials, or invented metrics.
- Keep dashboard text legible. Use a subtle 1 px border, soft shadow, and at most 8–12 px perspective or rotation.
- Use generous negative space and a restrained abstract background made from soft geometric planes or a very subtle grid.
- Use the repository/product mark only if it is taken from the real UI; do not invent a new logo.

## Master composition — 1600 × 900

- Background: `#070B18` to `#111827`, with a faint cool-gray radial lift behind the product.
- Copy block: left 38% of the canvas, vertically centered, 112 px safe margin.
- Dashboard: right 66%, overlapping the copy region slightly; crop only empty whitespace, never KPIs or charts.
- Title: 72–80 px, semibold, white.
- Subtitle: 30–36 px, medium, `#DCE6F7`.
- Supporting line: 19–22 px, `#9FB0C8`; keep on one line when possible.
- Optional eyebrow: `PRODUCTION-STYLE SALES OPERATIONS`, 14 px uppercase with wide tracking.
- Keep all critical content inside a 96 px safe area.

## Export matrix

| Asset | File | Dimensions | Adaptation |
| --- | --- | --- | --- |
| GitHub README Hero | `readme-hero.png` | 1600 × 900 | Master composition; maximize product legibility |
| GitHub Social Preview | `github-social-preview.png` | 1280 × 640 | Move copy upward/left; keep title and dashboard center inside 80 px safe area |
| LinkedIn Launch Image | `linkedin-launch.png` | 1200 × 627 | Keep headline to two lines maximum; preserve 64 px edge safety |
| Fiverr Portfolio Cover | `fiverr-portfolio-cover.png` | 1280 × 769 | Slightly taller dashboard crop; keep copy within central 80% for marketplace cropping |

Export all files as optimized sRGB PNGs. Do not upscale a low-resolution screenshot; re-capture the Dashboard at 1600 px wide if necessary.

## Image-editing prompt

```text
Create a premium, restrained B2B SaaS portfolio hero using the attached REAL SalesOps AI dashboard screenshot as the dominant product visual. Do not redraw, modify, replace, or invent any dashboard UI, numbers, charts, customer data, or logos. Place the real screenshot prominently in a clean graphite/midnight-navy composition with subtle geometric depth, a thin border, and a soft professional shadow. Avoid neon AI clichés, robots, glowing brains, fake customer logos, fake testimonials, and fake metrics.

Use this exact copy:
Title: SalesOps AI
Subtitle: AI-Powered Lead Qualification & Sales Automation
Supporting line: Explainable Lead Scoring • AI Sales Intelligence • Pipeline Automation

The result should feel like a credible enterprise SaaS launch image: modern, minimal, editorial, and legible. Preserve generous negative space and safe margins. Produce the requested target size without cropping any important dashboard KPI or chart.
```

Generate each target from the same master composition so color, typography, spacing, and screenshot treatment remain consistent.
