# DEMO_SCRIPT.md — Gokul Text Print AI Platform
## Client Demo Walkthrough — Sprint 8 RC1

---

## Setup Checklist (Before Demo)
- [ ] Both servers running: Flask (port 5001) and Next.js (port 3000)
- [ ] Open browser at http://localhost:3000
- [ ] Confirm dark mode is set for a premium first impression
- [ ] Upload at least one PDF to Knowledge Center beforehand

---

## Demo Flow (~20 minutes)

---

### Scene 1: Landing and Login (~2 min)

**What to do:** Open http://localhost:3000 — show the landing page.

**What to say:**
> "This is the Gokul Text Print AI Platform — your enterprise command center.
> Built specifically for textile printing operations, it brings together
> sales forecasting, inventory management, and AI-powered decision-making
> into a single executive interface."

**Action:** Click Login. Enter CEO credentials: ceo / ceo123

**What to say:**
> "The platform is role-secured. Our CEO user lands directly on the
> executive dashboard. The admin user has a separate operations center
> for system management."

---

### Scene 2: CEO Executive Dashboard (~4 min)

**What to show:** /dashboard — KPI cards, trend charts, alerts banner, recommendations

**What to say:**
> "The dashboard gives an at-a-glance view of the entire mill's health.
> Revenue performance, inventory value, AI-generated recommendations,
> and live operational alerts — all in one place, updated in real time."

**Highlight:**
- Point to the Business Health Score card: "This composite score reflects sales performance, inventory health, and alert severity — our AI's executive summary of where the mill stands today."
- Point to trend charts: "30-day revenue and volume trends show exactly where we are in the billing cycle."
- Click an alert to show it's actionable.

---

### Scene 3: Sales Intelligence (~3 min)

**What to show:** /sales — demand charts, product rankings, AI forecast, prediction history

**What to say:**
> "The Sales Intelligence module runs our AI Forecast Engine continuously.
> We see fabric-wise demand curves, top-performing products by volume,
> and the AI's recommendation for the next production cycle."

**Highlight:**
- Show the date range filter: "We can drill into any period — daily, weekly, monthly, or custom."
- Show prediction history table: "Every AI forecast is logged for audit — complete transparency."

---

### Scene 4: Inventory Intelligence (~3 min)

**What to show:** /inventory — stock levels, warehouse grid, slow-moving items, reorder AI

**What to say:**
> "Our Supply Intelligence Engine monitors over 50 fabric varieties
> across all storage bins in real time. When safety buffers drop below
> threshold, the system triggers an alert automatically."

**Highlight:**
- Show warehouse grid: "Each bin's occupancy, value, and alert status at a glance."
- Show the AI Simulator: "Our ops team can simulate any reorder scenario against the AI model before committing capital."

---

### Scene 5: AI Copilot (~4 min)

**What to show:** /copilot — type a question in the chat

**Sample question to type:**
> "What is our current inventory risk for Rayon Print fabric and what action should we take?"

**What to say:**
> "This is our AI Copilot — powered by a multi-agent architecture.
> The manager agent coordinates three specialized agents:
> a Sales Agent, an Inventory Agent, and a Knowledge Agent.
> Each contributes its expertise, and the system synthesizes a unified
> recommendation with a confidence score."

**Highlight:**
- Show the Sources section: "The answer is grounded in our own uploaded SOPs and company documents."
- Show the Reasoning section: "Full transparency — we see exactly which agents contributed and what data points they used."

---

### Scene 6: Knowledge Center (~2 min)

**What to show:** /knowledge — document library, semantic search

**What to say:**
> "Our Document Intelligence Engine processes any PDF — SOPs, machine
> manuals, chemical recipes, compliance documents. Once uploaded,
> the AI Copilot can search and reason over them instantly."

**Action:** Type a search query like "discharge printing safety threshold"

**What to say:**
> "This is semantic search — it understands meaning, not just keywords.
> It returns the exact paragraph from the relevant document."

---

### Scene 7: Reports Center (~2 min)

**What to show:** /reports — select Daily Briefing, click Download PDF

**What to say:**
> "Executive reports are generated on demand — daily, weekly, monthly,
> or any custom date range. PDF and CSV formats are both supported
> for board presentations or ERP integration."

---

### Scene 8: Alert Center (Admin Login — 1 min)

**Action:** Log out and log in as dmin / dmin123

**What to show:** /alerts — critical alerts, resolve one

**What to say:**
> "The Admin user has a full alert management dashboard.
> Critical incidents, stock alerts, and AI model errors are all tracked.
> Alerts can be marked resolved with a single click, creating a full audit trail."

---

## Key Talking Points

1. **100% live data** — No mocked charts or placeholder numbers
2. **Role-based access** — CEO sees business intelligence; Admin sees operations
3. **Multi-agent AI** — Three specialized agents + confidence scoring
4. **Audit trails** — Every AI recommendation and forecast is logged
5. **Dark/Light mode** — Optimized for factory floor (bright) and boardroom (dark)
6. **Mobile-ready** — Full functionality on tablet and mobile

---

## Fallback / FAQ

**Q: What if the AI Copilot is slow?**
> "The first query warms up the model — subsequent queries are faster.
> This is the Gemini 2.5 Flash model running on our secure infrastructure."

**Q: Can it connect to our ERP?**
> "The platform has an ERP integration layer built in — currently configured
> for Frappe/ERPNext. We can map your ERP fields in the integration sprint."

**Q: Is the data real?**
> "Yes — all data flows through our live SQLite database seeded with
> your actual historical sales and inventory patterns."
