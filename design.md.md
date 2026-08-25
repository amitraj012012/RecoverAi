# RecoverAI — Design System

## Purpose

This document defines the UI/UX and visual design system for **RecoverAI — AI Revenue Recovery Agent**.

The design should be:

- Simple
- Premium
- Financial/FinTech appropriate
- AI-native without looking gimmicky
- Fast to understand
- Mobile responsive
- Accessible
- Judge-friendly during a live hackathon demo

The visual goal is **“trustworthy financial intelligence + clear AI action.”**

---

# 1. UI/UX

## 1.1 Design Principles

### Clarity first
A judge should understand within 5 seconds:

1. How much revenue is at risk.
2. How much RecoverAI recovered.
3. What the AI is doing.
4. Why the AI selected an action.

### Business impact first

The primary dashboard hierarchy should be:

```text
Revenue Impact
    ↓
Recovery Performance
    ↓
AI Decisions
    ↓
Active Cases
    ↓
Detailed Analytics
```

Do not hide the most important financial metrics inside secondary pages.

### Simple, not empty

Use whitespace and clear hierarchy, but do not make the dashboard look unfinished.

### AI should feel controlled

Avoid excessive AI animations, glowing effects, or “magic” visuals.

The product should look like serious financial infrastructure with intelligent automation.

---

# 2. COLOR & THEME

## 2.1 Primary Theme

RecoverAI uses a **deep navy + electric blue + emerald** FinTech palette.

### Primary

```text
Deep Navy
#0B1220
```

Use for:
- Main navigation
- Dark surfaces
- Strong headings
- Important AI/system areas

### Primary Accent

```text
Electric Blue
#2563EB
```

Use for:
- Primary buttons
- Links
- Selected navigation
- AI actions
- Interactive elements

### Recovery / Success

```text
Emerald
#10B981
```

Use for:
- Revenue recovered
- Successful payment
- Positive growth
- Successful agent actions

### Warning

```text
Amber
#F59E0B
```

Use for:
- Revenue at risk
- Pending recovery
- Attention required

### Error

```text
Red
#EF4444
```

Use for:
- Failed payments
- Failed actions
- Critical errors

### Neutral surfaces

```text
White
#FFFFFF

Light Background
#F8FAFC

Border
#E2E8F0

Primary Text
#0F172A

Secondary Text
#64748B
```

---

# 3. THEME MODES

## Light mode

Default for the hackathon demo.

```text
Background: #F8FAFC
Cards: #FFFFFF
Text: #0F172A
Borders: #E2E8F0
Primary: #2563EB
Success: #10B981
Warning: #F59E0B
Error: #EF4444
```

## Dark mode

Optional.

```text
Background: #070B14
Cards: #0F172A
Text: #F8FAFC
Muted: #94A3B8
Primary: #3B82F6
Success: #34D399
```

Do not create two completely different visual systems. Keep components consistent.

---

# 4. COLOR SEMANTICS

Color must communicate meaning consistently.

```text
Blue    → AI / action / primary interaction
Green   → recovered / success / positive
Amber   → at risk / pending / attention
Red     → failed / critical
Gray    → neutral / inactive
Purple  → optional advanced AI insight
```

Never use color only to decorate a component when the same color already communicates a business state.

---

# 5. TYPOGRAPHY

## Font

Preferred:

```text
Inter
```

Fallback:

```text
system-ui, -apple-system, BlinkMacSystemFont, "Segoe UI", sans-serif
```

## Hierarchy

### Page title
```text
32px
font-weight: 700
```

### Section heading
```text
20–24px
font-weight: 600
```

### Card metric
```text
28–36px
font-weight: 700
```

### Body
```text
14–16px
```

### Secondary text
```text
12–14px
```

Use strong typography for financial numbers.

---

# 6. LAYOUT

## Desktop

Use:

```text
Sidebar
+
Main content
```

Example:

```text
┌──────────────┬─────────────────────────────────────┐
│              │ Header                              │
│   Sidebar    ├─────────────────────────────────────┤
│              │ Revenue Metrics                     │
│ Overview     │                                     │
│ Payments     │ AI Recovery Overview                │
│ Recovery     │                                     │
│ Customers    │ Charts / Cases                      │
│ Analytics    │                                     │
│ Settings     │                                     │
└──────────────┴─────────────────────────────────────┘
```

## Mobile

Use:

- Bottom navigation or collapsible sidebar.
- One-column cards.
- Horizontal scrolling only where necessary.
- Large touch targets.
- Avoid dense tables.

---

# 7. DASHBOARD DESIGN

## Top section

Show:

```text
Good morning, Merchant

Your AI recovery system recovered
₹31.2L this period.
```

Then primary metrics:

```text
┌──────────────┐ ┌──────────────┐
│ Revenue      │ │ Recoverable  │
│ at Risk      │ │ Revenue      │
│ ₹80L         │ │ ₹56L         │
└──────────────┘ └──────────────┘

┌──────────────┐ ┌──────────────┐
│ Recovered    │ │ Recovery     │
│ ₹31.2L       │ │ Rate 55.3%   │
└──────────────┘ └──────────────┘
```

Recovered revenue should be the strongest visual metric.

---

# 8. AI RECOVERY PANEL

Create a visually distinctive but restrained AI panel.

Example:

```text
┌─────────────────────────────────────────┐
│ ✦ RecoverAI                              │
│ AI Recovery Engine                       │
│                                         │
│ 1,284 cases analyzed                     │
│ 742 actions executed                     │
│ ₹8.4L recovered today                    │
│                                         │
│ [ View AI Decisions ]                    │
└─────────────────────────────────────────┘
```

Use a subtle blue accent, not a large glowing gradient.

---

# 9. RECOVERY CASE DESIGN

Each case should show:

```text
Customer
Payment Amount
Failure Reason
Recovery Probability
AI Strategy
Status
Recovered Amount
```

Example:

```text
C1024
₹1,999
Card declined

Recovery probability
87%

AI action
Payment Link

● Recovered
₹1,999
```

---

# 10. AI DECISION DETAIL

The most important judge-facing component.

Show:

```text
AI Decision

Recommended:
Create Payment Link

Confidence:
87%

Why:
Customer has 17 successful payments out
of 18 attempts. This appears to be an
isolated card failure, so a discount is
unnecessary.

Expected recovery:
₹1,739

[ Execute Action ]
```

The reasoning should be concise and understandable.

Do not expose hidden chain-of-thought or internal model reasoning. Show only a short decision rationale based on observable factors.

---

# 11. STATUS COMPONENTS

Use consistent badges.

```text
● Recovered       Green
● At Risk         Amber
● Analyzing       Blue
● Recovery Active Blue
● Failed          Red
● Escalated       Purple/Gray
```

Never rely on color alone. Include text/icon.

---

# 12. CHART DESIGN

Use charts only when they communicate useful information.

Recommended:

### Recovery funnel

```text
Failed
  ↓
Recoverable
  ↓
Recovery Started
  ↓
Recovered
```

### AI vs Baseline

Bar comparison:

```text
Baseline     ███████████
RecoverAI    █████████████████
```

### Revenue recovery trend

Line chart over time.

### Strategy performance

Bar chart:

```text
Retry
Payment Link
Alternate
Reminder
Incentive
```

Avoid decorative charts with no decision value.

---

# 13. BUTTONS

## Primary

Electric blue background.

Use for:
- Execute recovery
- Run simulation
- View AI decision

## Success

Emerald.

Use for:
- Confirm verified result
- Recovered state where an explicit action is required

## Secondary

Neutral border/background.

## Destructive

Red.

Use sparingly.

---

# 14. TABLES

Tables should be clean and compact.

Columns:

```text
Customer | Amount | Failure | Probability | Strategy | Status
```

Use:
- Sticky header when useful.
- Pagination.
- Search.
- Filters.
- Sort.
- Responsive mobile card transformation.

---

# 15. EMPTY STATES

Never show a blank screen.

Example:

```text
No recovery cases yet

Payment failures will appear here
when RecoverAI detects revenue at risk.

[ Load Demo Data ]
```

---

# 16. LOADING STATES

Use skeleton loaders for dashboards and tables.

For AI operations:

```text
Analyzing payment...
Checking customer history...
Selecting recovery strategy...
```

Do not use fake progress percentages.

---

# 17. ERROR STATES

Example:

```text
We couldn't execute the recovery action.

The payment simulator did not respond.

[ Retry ]   [ View Case ]
```

Never expose stack traces.

---

# 18. RESPONSIVE DESIGN

Must support:

- Desktop
- Laptop
- Tablet
- Mobile

Primary demo target:

```text
1440 × 900
```

Secondary:

```text
390 × 844
```

No horizontal scrolling on normal pages.

---

# 19. ACCESSIBILITY

Requirements:

- Keyboard navigation.
- Visible focus states.
- Accessible labels.
- Good contrast.
- Semantic HTML.
- Touch targets at least approximately 44px where practical.
- Icons should not be the only source of meaning.

---

# 20. ANIMATION

Use subtle animation only for:

- Page transitions.
- Metric updates.
- Agent status.
- Chart rendering.
- Button feedback.

Avoid:
- Excessive particles.
- Constant glowing effects.
- Long animations.
- Distracting AI “brain” animations.

The product should feel fast and trustworthy.

---

# 21. JUDGE-FIRST DEMO DESIGN

The first screen should communicate:

```text
₹80L
Revenue at Risk

₹31.2L
Recovered

55.3%
Recovery Rate
```

Then immediately show:

```text
AI recovered revenue
↓
How?
↓
Customer case
↓
AI decision
↓
Action
↓
Verified payment
```

The judge should understand the value without needing a long explanation.

---

# 22. BRAND DIRECTION

RecoverAI should feel:

```text
Trustworthy
Intelligent
Financial
Modern
Fast
Professional
```

Avoid making it look like:

```text
Generic AI chatbot
Crypto dashboard
Gaming UI
Over-designed futuristic AI product
```

---

# 23. MEMORY & UI PREFERENCES

If user preferences are implemented later, support:

- Light/dark mode.
- Sidebar collapsed/expanded state.
- Table density.
- Preferred dashboard layout.

Do not store unnecessary personal information.

---

# 24. DESIGN DO / DON'T

## DO

- Use whitespace.
- Use consistent cards.
- Highlight recovered revenue.
- Keep AI decisions explainable.
- Use restrained blue/green accents.
- Make financial numbers prominent.
- Keep interactions fast.

## DON'T

- Use random colors.
- Overuse gradients.
- Put every metric on the home page.
- Use huge AI illustrations.
- Use unnecessary animations.
- Hide important actions.
- Make the dashboard look like a template.

---

# 25. DESIGN SUCCESS CRITERIA

The design is successful if a new viewer can understand within approximately 10 seconds:

1. What RecoverAI does.
2. How much revenue is at risk.
3. How much revenue was recovered.
4. That AI is making recovery decisions.
5. That actions are actually executed and verified.

The UI should support the product story:

**Failed Payment → AI Understands → AI Decides → AI Acts → Payment Verified → Revenue Recovered**
