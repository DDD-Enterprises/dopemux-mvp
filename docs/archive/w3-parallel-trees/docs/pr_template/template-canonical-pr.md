---
id: CANONICAL_PR_TEMPLATE
title: Canonical Pr Template
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Canonical Pr Template (explanation) for dopemux documentation and developer
  workflows.
---
# 🚀 Mission Summary
> A clear, fast read on what this PR changes and why it matters.

## ✨ What changed
-

## 🎯 Why this matters
-

---

# 🧭 Context Linkage
> Ground this change in real context so reviewers are not forced to mind-read.

## 🧩 Problem / motivation
-

## 🔗 Linked context
- Issue:
- Doc:
- ADR:
- Incident:
- Other:

---

# 🧪 Verification Matrix
> Log what was **actually** verified. If something was not checked, say so plainly.

## ✅ Checks performed
- [ ] Unit tests
- [ ] Integration tests
- [ ] Lint
- [ ] Typecheck
- [ ] Build
- [ ] Manual verification
- [ ] Docs/examples checked
- [ ] Migration/config verification

## 🖥️ Commands / CI evidence
```text
# commands, CI jobs, or proof references
```

📡 Results
• ⚠️ Not verified / gaps
•

⸻

⚠️ Risk Surface
Name the blast radius honestly. Reviewers should know what could break before they approve.

🌡️ Risk level
• Low
• Medium
• High
• Critical

🛰️ Affected surfaces
• API
• DB / schema / migration
• Config / infra
• Auth / permissions
• Performance
• UX / behavior
• Docs only
• Internal refactor only
• Other:

🧨 Known risks
•

⸻

🛟 Rollback Protocol
If this goes sideways, how do we unwind it without improvising under pressure?

↩️ Rollback plan
•
⛔ Rollback cautions
•

⸻

👀 Reviewer Flight Deck
Tell reviewers where to focus so they spend time on the right risks.

🔬 Review focus areas
•
❓ Open reviewer questions
•
📍 Known follow-ups
•

⸻

🌌 High-Risk Integration Notes
Fill this section only for semantic merges, arbitration-lane cases, major migrations, or conflict-heavy integrations.

🧠 Why this is high risk
•
⚖️ Candidate end states considered
•
🧭 Manual decisions still required
•
🧪 Additional verification required before merge
•

⸻

✅ Launch Checklist
Check only what is true. The automation layer may validate this against evidence.

• I described the change clearly.
• I explained why this PR exists.
• I linked the relevant context.
• I documented the verification truthfully.
• I documented verification gaps, if any.
• I documented known risks.
• I documented rollback steps.
• I added reviewer guidance where needed.
• I completed the High-Risk Integration Notes section if this PR needs it.

⸻

🛠️ Operator / Maintainer Notes
Optional operational notes for merge, sequencing, rollout, or supervision.

🚦 Queue / merge considerations
•
🧬 Deployment / sequencing notes
•
🛰️ Operator notes
•
