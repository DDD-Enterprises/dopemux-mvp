# Prompt 2 Final Forensic Audit

## RTE model research cross-audit against the canonical handoff pack

This final artifact treats `prompt1_handoff_pack_normalized.md` as the **current-state authority** for canonical naming, route normalization, evidence labels, lifecycle/capability notes, benchmark-only unknowns, control models, and preserved Prompt 1 routing hypotheses. The three reports remain **hypotheses under audit**, not source-of-truth registries. Uncertainty labels are preserved exactly as the handoff pack defines them: `CONFIRMED`, `PARTIAL`, `INFERRED`, `CLAIMED`, `UNKNOWN`, `CONFLICTING`, and `DISPUTED`.  

Surface separation is mandatory throughout this report: **direct-provider APIs**, **OpenRouter routes / routed model IDs**, **chat or subscription surfaces**, and **local/open-weight deployments** are distinct comparison classes and must not be flattened into one bucket. Report A states this explicitly, and the handoff pack’s route/type normalization supports the same rule.  

---

## Executive verdict on each report

### Report A

**Verdict: keep, but only as a surface/governance and systems-risk audit. Do not use it as canonical model truth.** Report A is strongest on comparison taxonomy, governance posture, batch support, OpenRouter route behavior, and OpenClaw/operator-surface implications. Its weakness is registry discipline: it mixes direct-provider models, routed surfaces, local/open-weight lanes, and chat-adjacent comparisons more broadly than the handoff pack’s current canonical registry allows.   

### Report B

**Verdict: keep as the best RTE routing-brain draft, but rebase it onto the handoff pack before using it downstream.** Report B is the strongest document for step-scoped RTE routing, structured JSON discipline, escalation logic, cost tiers, and validator-aware policy. Its main problem is not conceptual weakness but registry drift: it promotes several direct-provider candidates that are not part of the current handoff-pack canonical set.   

### Report C

**Verdict: keep as the OpenRouter extension and free/cheap candidate expansion, but downgrade many operational claims from “portfolio fact” to “experiment-worthy hypothesis.”** Report C is strongest on OpenRouter free-lane economics, hidden-value candidate discovery, and RTE lane proposals for cheap or zero-cost experimentation. Its main defects are lifecycle fragility, over-optimistic use of free lanes, and repeated conversion of product-page positioning into routing certainty.   

---

## Canonical correction summary

The corrected rule set is simple, because apparently three reports still managed to overcomplicate it:

1. **The handoff pack is the current-state authority artifact.** Anything outside it is an **out-of-registry candidate**, not silently canonical truth.  

2. **Prompt 1 routing hypotheses remain hypotheses.** They are preserved for planning, not promoted to settled truth. That includes claims about the strongest free structured-output candidate, strongest free code-aware candidate, strongest cheap bulk extractor, and control anchors. 

3. **Benchmark-only unknowns stay benchmark-only unknowns.** The handoff pack explicitly leaves provider throttling, long-context economics, tool correctness, provider spread, batch behavior, residency posture, judge quality, and repair quality unresolved. No report gets to “win” those by sounding confident.  

4. **StepFun lifecycle is not resolved.** The handoff pack and Report C preserve a sunsetting note for `stepfun/step-3.5-flash:free`; in this final artifact it remains a **stale/disputed handoff-pack field** and **not a safe planning fact**. It is retained only as a warning and as a live-revalidation target.  

---

## Invalid-name and stale-claim matrix

This matrix is derived from the handoff pack’s canonical registry plus the claims made in Reports A, B, and C.  

| item as used in reports                                        | audit status                     | classification                                          | reason                                                                                                                                                                              |
| -------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| `openai/gpt-4.1`, `openai/gpt-4.1-mini`, `openai/gpt-4.1-nano` | keep                             | current-state authority                                 | These are preserved as control / production anchors in the handoff pack.                                                                                                            |
| `anthropic/claude-sonnet-4`                                    | keep                             | current-state authority                                 | Preserved in Prompt 1 routing hypotheses and control/judge roles.                                                                                                                   |
| `google/gemma-4-31b-it:free`                                   | keep                             | current-state authority with PARTIAL routing hypothesis | Canonical in the handoff pack; also preserved as the strongest doc-supported free structured-output candidate hypothesis, not settled truth.                                        |
| `qwen/qwen3-coder:free`                                        | keep, but constrained            | current-state authority with PARTIAL routing hypothesis | Canonical in the handoff pack, but only partially supported for code-aware extraction/repair, not proven strict-JSON safe.                                                          |
| `minimax/minimax-m2.5:free`                                    | keep, but constrained            | current-state authority with PARTIAL routing hypothesis | Canonical in handoff pack; suitable as experimental bulk-extraction hypothesis only.                                                                                                |
| `gpt-5.4`, `gpt-5.4-mini`, `gpt-5.4-nano`, `gpt-5.4-pro`       | verify before adoption           | out-of-registry candidate                               | Report A/B treat them as central, but they are not in the current handoff-pack canonical set. They may be valid market candidates, but not current-state canonical planning keys.   |
| `claude-sonnet-4-6`, `claude-opus-4-6`                         | verify before adoption           | out-of-registry candidate                               | Used heavily in Report B, but not normalized into the handoff-pack current registry.                                                                                                |
| `google/gemini-2.5-pro`                                        | verify before adoption           | out-of-registry candidate                               | Relevant in Report B as lifecycle-risk example, but not part of the handoff-pack canonical current-state set.                                                                       |
| `stepfun/step-3.5-flash:free` “going away April 9, 2026”       | do not treat as settled          | stale/disputed handoff-pack field                       | Preserved in the handoff pack and Report C, but retained here only as a disputed lifecycle note requiring live revalidation.                                                        |
| `openrouter/free` used as an evaluation router                 | keep only for ad-hoc prototyping | route key, not model                                    | Report C correctly treats it as experiment-only; it is a random routed free pool, not a stable benchmark model.                                                                     |

---

## Surface-mismatch and route-mismatch matrix

This is where humans keep making the same stupid category error with better formatting. Report A is explicit that these surfaces must not be mixed, and the handoff pack’s normalization model agrees.  

| mismatch type                                                       | where it appears                 | audit judgment                                                                                                                                                                  |
| ------------------------------------------------------------------- | -------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| direct-provider APIs vs OpenRouter-routed IDs                       | mostly A and B vs C/handoff pack | **Major mismatch.** B often discusses direct-provider IDs while C and the handoff pack normalize around OpenRouter keys. These are not directly equivalent planning surfaces.   |
| routed route key vs stable model ID                                 | C                                | **Major mismatch risk.** `openrouter/free` is a router surface, not a reproducible model. Fine for smoke tests, bad for measurement-grade comparisons.                          |
| subscription/chat surface vs token-billed API                       | A                                | **Correctly flagged by A.** These should never be blended into one benchmark lane unless benchmarking operator economics itself.                                                |
| local/open-weight vs hosted API                                     | A                                | **Correctly flagged by A.** Local/open-weight lanes shift the problem to hardware, quantization, tool formatting, and ops. They are separate deployment classes.                |
| coding-specialized vs general extraction models                     | A, B, C                          | **Partially respected, still messy.** A says to separate them; B and C sometimes mix code-aware lanes into broader extraction recommendations without enough guardrails.        |
| deep-research or tool-integrated agent surfaces vs plain generation | A                                | **Correctly flagged by A, under-covered elsewhere.** This remains a real fairness hazard for Prompt 3.                                                                          |

---

## Evidence quality matrix

The handoff pack’s evidence framework controls here: source basis, confidence, and verification status matter more than how polished the prose sounds. Shocking, I know. 

| claim class                                      | Report A      | Report B | Report C | final judgment                                                                                        |
| ------------------------------------------------ | ------------- | -------- | -------- | ----------------------------------------------------------------------------------------------------- |
| surface taxonomy and comparison hygiene          | strong        | moderate | moderate | **A wins.** Best supported and most operationally useful.                                             |
| strict JSON / structured-output routing          | moderate      | strong   | strong   | **B and C win.** Best aligned with handoff-pack benchmark needs and schema-gated routing.             |
| cost-tier routing and escalation                 | weak-moderate | strong   | moderate | **B wins.** It is the cleanest routing-brain document.                                                |
| OpenRouter free-lane economics                   | moderate      | moderate | strong   | **C wins.** Strongest on free-lane constraints and cheap/zero-cost candidate framing.                 |
| governance, residency, retention, chain-of-trust | strong        | weak     | weak     | **A wins.** B and C under-cover governance badly relative to deployment risk.                         |
| batch support and bulk processing economics      | strong        | weak     | weak     | **A wins.** The handoff pack also marked batch as unresolved, which makes A especially useful here.   |
| “this model behaves well” style claims           | mixed         | mixed    | weak     | **Downgrade across the board.** Those belong in the harness, not in doctrine.                         |

---

## Economics and batch-support audit

Report A is the only document that treats batch as a first-class economic primitive rather than an afterthought. It documents batch support for OpenAI API, Gemini API, Vertex routes, and xAI existence, while noting OpenRouter is not a native batch API surface. The handoff pack simultaneously marks batch behavior as a benchmark-only unknown for current planning, which means B and C simply do not cover this area adequately.  

**Audit result:**

* **Keep from Report A:** OpenAI batch, Gemini batch, Vertex batch, and the warning that batch semantics differ across surfaces. 
* **Drop as incomplete from B/C:** any implicit assumption that “cheap online calls” are enough to model production economics. Neither document adequately addresses async bulk execution or queue semantics.  
* **Prompt 3 implication:** batch support must become an explicit benchmark dimension, not an optional appendix, because the handoff pack says it is still unresolved. 

---

## Rate-limit / latency / uptime audit

Report C is strongest on free-tier rate limits and throughput realism. It clearly frames the OpenRouter free lane as **research-only**, not production, because quotas, throttling, and failed-attempt counting make the zero-cost profile operationally brittle. Report A is stronger on uptime routing behavior through OpenRouter fallbacks. Report B contributes a useful revalidation target set, including provider uptime, error rate, and retry churn.   

**Audit result:**

* **Keep:**

  * free-tier hard-cap framing from C,
  * fallback / provider-routing uptime framing from A,
  * monthly revalidation targets from B.   
* **Verify later:** actual peak-hour throttling, timeout variance, latency under fallback, and route-specific error rate. The handoff pack explicitly leaves these as `UNKNOWN`. 
* **Do not preserve as settled truth:** any claim that a free route is an acceptable production lane. That is fantasy dressed as thrift.  

---

## Data-risk and governance audit

Report A is the only report doing real adult supervision here. It builds a provider/risk matrix across OpenAI direct, Gemini direct, Vertex, OpenRouter, Alibaba Model Studio, and xAI, and it frames data risk in terms of residency clarity, retention/logging controls, and intermediary chain complexity. The handoff pack separately marks residency and data-handling posture as benchmark-only / unresolved for current-state planning.   

**Audit result:**

* **Strong keep:** A’s distinction between direct-provider routes, routed intermediary surfaces, and governance-sensitive open or foreign-provider lanes. 
* **Correct downgrade:** B and C may be fine for performance planning, but they are incomplete as deployment guidance because they under-cover retention, residency, ZDR, logging, and provider-policy variability.  
* **Current-state limitation:** the handoff pack still leaves residency/data-handling posture unresolved, so production routing cannot treat this as closed. 

---

## RTE relevance audit

The handoff pack already defines confirmed RTE datasets and step types, including small/medium/large repo cases, entity extraction, config extraction, API surface summarization, contradiction detection, JSON repair, and final synthesis. Reports A, B, and C are useful to the extent they support those exact lanes. 

| report | prescan / routing | extraction | repair / retry |     synthesis | coding/tool-heavy | free-entry onboarding | cost-sensitive routing |
| ------ | ----------------- | ---------: | -------------: | ------------: | ----------------: | --------------------: | ---------------------: |
| A      | moderate          |   moderate |           weak |      moderate |            strong |              moderate |               moderate |
| B      | strong            |     strong |         strong |        strong |          moderate |                  weak |                 strong |
| C      | moderate          |     strong |       moderate | weak-moderate |          moderate |                strong |                 strong |

**Final RTE judgment:**

* **Use A** for surface hygiene, governance constraints, and batch-aware planning.  
* **Use B** as the primary routing-brain source for Prompt 3.  
* **Use C** for the alternative-cost portfolio and free/cheap candidate watchlist, but only under strict experimental labeling.  

---

## OpenClaw relevance audit

Only Report A gives OpenClaw serious treatment. It includes a direct OpenClaw suitability shortlist and a local/open-weight fallback lane. That makes A the only report materially relevant to OpenClaw planning today. B and C are RTE-first and only indirectly useful to OpenClaw through routing and structured-output discipline.  

| report | OpenClaw value | audit judgment                                                             |
| ------ | -------------- | -------------------------------------------------------------------------- |
| A      | high           | keep as primary OpenClaw relevance source                                  |
| B      | medium-low     | keep only for escalation logic, JSON discipline, and cost tiers            |
| C      | medium-low     | keep only for cheap alternative lanes and experimental candidate expansion |

**Final OpenClaw judgment:**

* **Strong primary relevance:** A. 
* **Secondary relevance:** B for deterministic escalation, retry containment, and schema constraints. 
* **Experimental relevance:** C for low-cost or alternative surface scouting. 

---

## Contradiction matrix across reports

| topic                                                          | Report A             | Report B                          | Report C                           | adjudication                                                                                                                      |
| -------------------------------------------------------------- | -------------------- | --------------------------------- | ---------------------------------- | --------------------------------------------------------------------------------------------------------------------------------- |
| strict JSON should drive routing                               | implied, not central | central                           | central                            | **B/C stronger.** This aligns best with handoff-pack harness metrics and validator framing.                                       |
| free-entry profile viability                                   | sandbox tone         | not central                       | explicit “research-only”           | **C best supported.** Free entry exists, but only experimentally.                                                                 |
| governance/residency importance                                | central              | under-covered                     | under-covered                      | **A wins.** This is not optional for production routing.                                                                          |
| batch economics matter                                         | central              | weak                              | weak                               | **A wins.** B/C materially under-cover this.                                                                                      |
| direct-vs-routed-vs-chat-vs-local surfaces must stay separate  | central              | only partly implicit              | only partly implicit               | **A wins.** This should be enforced in Prompt 3.                                                                                  |
| StepFun free lifecycle                                         | not central          | not central                       | treated as concrete lifecycle fact | **Disputed / stale.** Preserve only as a revalidation flag, not planning truth.                                                   |
| control anchors should remain GPT-4.1 family + Claude Sonnet 4 | compatible           | partly superseded by GPT-5.x in B | preserved in C production_default  | **Handoff pack governs.** Current control anchors stay as preserved Prompt 1 controls until registry is intentionally updated.    |

---

## Coverage-gap matrix

The handoff pack itself tells you what still is not known. Convenient, really. Humans occasionally write something useful. 

| missing area                                           | status after A/B/C       | final judgment                    |
| ------------------------------------------------------ | ------------------------ | --------------------------------- |
| structured JSON pass-rate by model and lane            | still missing            | benchmark-only unknown            |
| tool/function-calling correctness                      | still missing            | benchmark-only unknown            |
| provider spread / endpoint resilience                  | still missing            | benchmark-only unknown            |
| batch behavior as comparable routing dimension         | partly covered by A only | still open for Prompt 3           |
| residency / data-handling posture in canonical handoff | not closed               | still open; governance blocker    |
| free-vs-paid fairness under identical harness settings | missing                  | benchmark-only unknown            |
| rate-limit / peak-hour behavior                        | not closed               | benchmark-only unknown            |
| retry sensitivity curves                               | not closed               | benchmark-only unknown            |
| control-model sufficiency                              | not closed               | benchmark-only unknown            |
| OpenClaw-specific tool-loop reliability                | mostly missing           | Prompt 3 should add it explicitly |

---

## Keep / drop / verify-later decisions for major claims

| claim                                                                                                              | decision                         | status label                                            |
| ------------------------------------------------------------------------------------------------------------------ | -------------------------------- | ------------------------------------------------------- |
| handoff pack governs canonical naming and evidence labels                                                          | keep                             | current-state authority                                 |
| control anchors remain `openai/gpt-4.1-nano`, `openai/gpt-4.1-mini`, `openai/gpt-4.1`, `anthropic/claude-sonnet-4` | keep                             | current-state authority / PARTIAL routing hypothesis    |
| strict JSON must use explicit structured-output-capable surfaces                                                   | keep                             | high-confidence operational rule                        |
| hybrid routing with direct-provider truth-core and OpenRouter fallback                                             | keep                             | supported design hypothesis                             |
| true $0 entrance profile exists only experimentally                                                                | keep                             | preserved Prompt 1 / C hypothesis, not production truth |
| Gemma 4 free as strongest doc-supported free structured-output candidate                                           | keep with caution                | PARTIAL routing hypothesis                              |
| Qwen3 coder free as strongest free code-aware candidate                                                            | verify later                     | PARTIAL routing hypothesis                              |
| MiniMax M2.5 free as strongest free bulk-extraction candidate                                                      | verify later                     | PARTIAL routing hypothesis                              |
| Hermes 4 70B as strong cheap structured-output/judge dark horse                                                    | verify later                     | PARTIAL routing hypothesis                              |
| DeepSeek V3.2 as strong cheap bulk-extraction candidate                                                            | verify later                     | PARTIAL routing hypothesis                              |
| Llama 4 Scout as strongest ultra-low-cost long-context control                                                     | verify later                     | INFERRED routing hypothesis                             |
| GPT-5.4 family should replace handoff controls immediately                                                         | drop for current-state planning  | out-of-registry candidate                               |
| Claude 4.6 / Gemini 2.5 Pro should be treated as current-state canonical                                           | drop for current-state planning  | out-of-registry candidate                               |
| StepFun free “going away April 9, 2026”                                                                            | do not preserve as settled truth | stale/disputed handoff-pack field                       |

Sources:     

---

## Corrected consolidated truth set for downstream planning

1. **Use the handoff pack as the only current-state registry backbone.** Do not silently replace it with broader market inventories from A or B.  

2. **Treat all Prompt 1 routing ideas as hypotheses awaiting harness validation.** Preserve them, but do not flatten them into facts. 

3. **Keep the current control-model baseline stable** until Prompt 3 proves replacement candidates under identical harness settings.  

4. **For RTE, the routing brain should inherit from Report B first**, especially step-scoped escalation, JSON-critical routing, repair isolation, and cost-tier rules.  

5. **For governance, residency, and chain-of-trust, inherit from Report A first.** B and C are insufficient on their own.  

6. **For cheap and zero-cost alternative lanes, inherit from Report C only as an experimental extension.** Free-lane and cheap-lane candidates are useful for Prompt 3 portfolio design, not for immediate production truth.  

7. **Keep surfaces distinct in all downstream tables and harness outputs:** direct-provider API, OpenRouter-routed, chat/subscription, and local/open-weight. 

8. **Retain StepFun only as a disputed lifecycle watch item.** It is not a trustworthy anchor for portfolio design.  

---

## Questions that can ONLY be answered by live benchmarking

The handoff pack is explicit here, and it is right. Documentation cannot answer these. Reports A/B/C do not answer these. Your future self will answer these by running the damn harness. 

* Which models achieve the best **first-pass valid JSON %** by lane? 
* Which models achieve the best **validator pass %** under the exact RTE schemas? 
* What is the real **retry sensitivity curve** per lane and model? 
* What is the true **provider throttling / peak-hour error profile**? 
* Does longer context improve **cost-per-success** or just inflate outputs? 
* Which models have reliable **tool/function-calling correctness** under RTE tool schemas? 
* Which routes provide meaningful **provider spread / resilience** in practice? 
* Which repair lanes actually improve malformed outputs without inventing fields? 
* Are current control anchors sufficient, or do out-of-registry candidates materially outperform them under fair settings? 
* What is the actual **free-tier completion rate before quota exhaustion** for real RTE runs? 
* What is the real **batch advantage** once async execution, quotas, and artifact validation are included? 
* What is the enforceable **residency / data-handling posture** per route once provider selection and fallback are pinned? 

---

## Recommendations for Prompt 3 and benchmark-harness design

Prompt 3 should not re-litigate the model market like a caffeinated pundit. It should operationalize the already-audited truth set.

### 1. Lock the authority model

Use the handoff pack as the canonical registry input and add a separate section for **out-of-registry candidates**. Do not merge the two. 

### 2. Enforce surface isolation

Every benchmark record should include a required surface field:

* `direct_provider_api`
* `openrouter_routed`
* `chat_or_subscription_surface`
* `local_or_open_weight`
  This is non-negotiable. 

### 3. Use the handoff-pack metrics as the default scoreboard

At minimum capture:

* first-pass valid JSON %
* validator pass %
* retries per step
* median tokens
* timeouts
* request error rate
* latency variance
* expected total cost
* quota consumption in free mode 

### 4. Keep the handoff-pack step types

Prompt 3 should benchmark across:

* small repo
* medium repo
* large repo / monorepo
* entity extraction from code
* config extraction
* API surface summarization
* contradiction detection
* JSON repair
* final synthesis 

### 5. Preserve current controls

Prompt 3 should always include `openai/gpt-4.1-mini` and `openai/gpt-4.1` as fixed controls, because the handoff pack says fair comparison requires anchored controls.  

### 6. Separate “production” from “experiment”

Adopt three portfolio classes:

* **current-state authority**
* **out-of-registry candidate**
* **benchmark-only unknown**
  This prevents the usual human habit of turning a promising experiment into an operational promise after one good afternoon.  

### 7. Explicitly quarantine disputed lifecycle items

Keep `stepfun/step-3.5-flash:free` in a **stale/disputed lifecycle watchlist**, not in the production candidate pool.  

### 8. Inherit the best parts of each report

* from **A**: comparison taxonomy, governance audit, batch lens, OpenClaw/operator relevance
* from **B**: routing brain, escalation logic, JSON-critical design
* from **C**: cheap/free extension set and experimental YAML/profile ideas   

### 9. Add two explicit Prompt 3 no-go rules

* no random-router results in measurement-grade comparisons (`openrouter/free` only for ad-hoc smoke tests) 
* no mixing of chat/subscription outputs with API results in the same benchmark family 

### 10. Treat governance as a gate, not a note

Prompt 3 should include a governance gate that can exclude otherwise-good candidates when residency, logging, retention, or intermediary posture is unresolved. Report A makes clear why. 
