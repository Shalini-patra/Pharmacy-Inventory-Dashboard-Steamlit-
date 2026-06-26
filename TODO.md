# TODO - Executive Overview + Theme/UX Redesign

## Step 1: Repo understanding refresh
- [x] Read `app.py`, `pages/1_Executive_Overview.py`, `lib/theme.py`, `lib/colors.py`, `lib/db.py`.
- [x] Identify where KPI cards/tooltips are used across pages (beyond Executive Overview).


## Step 2: Global theme system fix (Parts 1–4)
- [x] Update `lib/theme.py` palettes + CSS to fully apply Light theme.

- [x] Ensure page background/container backgrounds/borders match required hex codes.
- [x] Ensure Plotly backgrounds/text/grid colors follow theme.
- [ ] Add KPI tooltip styling support (later used by all pages).


## Step 3: Global header + sidebar styling (Parts 2–3)
- [ ] Update shared header banner rendering on all pages.
- [ ] Update sidebar background/selected/hover states.

## Step 4: Executive Overview redesign (Parts 5–6)
- [ ] Move filters into sidebar with slicer-like behavior.
- [ ] Implement filter cascade across all Executive Overview visuals.
- [ ] Rebuild Top/Bottom moving drugs charts + tables with required gradients and tooltips.
- [ ] Rebuild Revenue vs Profit dual-axis area chart (last 12 months).
- [ ] Rebuild Weekday/Hour heatmap (color intensity only; tooltips).
- [ ] Add meaningful KPI tooltips and restyle KPI cards per theme rules.

## Step 5: Database/query changes (Part 7)
- [ ] Add/update DB functions for: top/bottom by units (last 30d), monthly revenue+profit (12 months), hourly heatmap, distinct filter values.
- [ ] Implement a shared/global filter application approach to avoid duplicated SQL.

## Step 6: Code quality + helpers (Part 8)
- [ ] Create reusable KPI card component.
- [ ] Create reusable chart styling helpers.
- [ ] Create reusable filter UI helpers.
- [x] Create shared UI override helper for header/sidebar styling (`lib/ui_overrides.py`).


## Step 7: Responsiveness (Part 9)
- [ ] Verify layout on wide and narrow widths; ensure no overflow/clipping.

## Step 8: Testing
- [ ] Run `streamlit run app.py` and validate theme toggle.
- [ ] Validate Executive Overview filters + all visuals respond.
- [ ] Validate tooltips work.

