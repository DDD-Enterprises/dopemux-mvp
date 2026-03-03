# Documentation Review Checklist

*Quick reference for reviewing RFC, ADR, and arc42 documentation in Dopemux*

## 🚀 Quick Start

**For Reviewers:** Use this checklist to ensure consistent, thorough reviews
**For Authors:** Self-review before requesting formal review
**For LLMs:** Automated validation criteria for documentation quality

---

## RFC Review Checklist

### 📋 Structure & Metadata
- [ ] **YAML front-matter complete** with all required fields
- [ ] **ID follows convention**: `rfc-YYYY-XXX-feature-name`
- [ ] **Status appropriate**: draft/review/accepted/rejected/superseded
- [ ] **Reviewers assigned** and tagged correctly
- [ ] **Tags relevant** to content and feature area
- [ ] **ADHD metadata included**: cognitive load, attention state, reading time

### 📝 Content Quality
- [ ] **Problem statement clear** and one-sentence summary provided
- [ ] **Why it matters** explicitly stated with business/user impact
- [ ] **Context comprehensive** with background, constraints, dependencies
- [ ] **Options analysis thorough** with at least 2-3 viable alternatives
- [ ] **Pros/cons table complete** for all options
- [ ] **Proposed direction justified** with clear reasoning
- [ ] **Open questions identified** and categorized (critical vs nice-to-know)
- [ ] **Risks enumerated** with probability, impact, and mitigation
- [ ] **Timeline realistic** with concrete phases and milestones

### 🧠 ADHD Accommodation Review
- [ ] **Cognitive load appropriate** for target audience
- [ ] **Visual structure clear** with tables, bullets, and headers
- [ ] **Progressive disclosure** - essential info first, details follow
- [ ] **Context anchoring** - decision linked to business goals
- [ ] **Options comparison visual** and easy to scan
- [ ] **Action items specific** and achievable within attention spans

### 🔗 Integration & Links
- [ ] **Related work referenced** with proper links
- [ ] **Dependencies identified** and realistic
- [ ] **Follow-up work scoped** appropriately
- [ ] **Success metrics defined** and measurable

---

## ADR Review Checklist

### 📋 Structure & Metadata
- [ ] **YAML front-matter complete** with all required fields
- [ ] **ID follows convention**: `adr-XXX-descriptive-name`
- [ ] **Status appropriate**: proposed/accepted/rejected/superseded
- [ ] **Derived from RFC** if applicable
- [ ] **Supersession relationships** documented if replacing/replaced by other ADRs
- [ ] **ADHD metadata included**: complexity, cognitive load, context switching impact

### 📝 Content Quality
- [ ] **Context & problem clear** with situation and forces explained
- [ ] **Decision drivers complete** with functional requirements, quality goals, constraints
- [ ] **Options considered** and briefly described
- [ ] **Decision outcome explicit** with chosen option clearly stated
- [ ] **Justification thorough** with primary reasons explained
- [ ] **Consequences documented** - positive, negative, and neutral
- [ ] **Trade-offs acknowledged** honestly
- [ ] **Implementation requirements** specific and actionable

### 🧠 ADHD Impact Analysis
- [ ] **Cognitive load impact** assessed and explained
- [ ] **Context switching effects** considered
- [ ] **Executive function support** evaluated
- [ ] **Attention management** implications documented
- [ ] **User experience impact** on ADHD developers addressed

### ✅ Validation & Implementation
- [ ] **Success criteria measurable** and specific
- [ ] **Testing approach defined** for validation
- [ ] **Monitoring strategy** included
- [ ] **Follow-up actions** clearly listed
- [ ] **Dependencies identified** and realistic

---

## arc42 Section Review Checklist

### General Standards
- [ ] **Section purpose clear** and aligned with arc42 template
- [ ] **Stakeholder relevance** appropriate for intended audience
- [ ] **Cross-references present** to related sections and ADRs
- [ ] **Visual aids included** where helpful (diagrams, tables)
- [ ] **ADHD-friendly formatting** with progressive disclosure

### Section-Specific Checks

#### Section 1: Introduction & Goals
- [ ] **Business goals clear** and measurable
- [ ] **Stakeholders identified** with roles and interests
- [ ] **Quality goals limited** to 3-5 key items
- [ ] **Success criteria defined** for project/system

#### Section 3: Context & Scope
- [ ] **System boundary explicit** and well-defined
- [ ] **External interfaces documented** with protocols
- [ ] **Context diagram present** and current
- [ ] **Scope limitations clear** (what's NOT included)

#### Section 5: Building Block View
- [ ] **Component responsibilities clear** and non-overlapping
- [ ] **Interfaces well-defined** with contracts
- [ ] **Hierarchy logical** and easy to follow
- [ ] **C4 Level 1/2 diagrams** present and current

#### Section 6: Runtime View
- [ ] **Scenarios representative** of key use cases
- [ ] **Sequence diagrams clear** and detailed
- [ ] **Error handling included** in behavioral flows
- [ ] **Performance characteristics** documented

#### Section 9: Architecture Decisions
- [ ] **ADR list current** and complete
- [ ] **Status tracking accurate** for all decisions
- [ ] **Links functional** to actual ADR documents
- [ ] **Impact assessment** clear for major decisions

---

## Quality Gates

### Minimum Viable Documentation
**Before Review:**
- [ ] All required sections present
- [ ] YAML metadata complete
- [ ] Links functional
- [ ] Spell-check passed

**Before Approval:**
- [ ] Technical review completed
- [ ] ADHD accommodation review passed
- [ ] Integration verified with existing docs
- [ ] Follow-up work identified and planned

### Excellence Standards
**For High-Impact Decisions:**
- [ ] Multiple reviewer feedback incorporated
- [ ] Prototyping results included
- [ ] Performance implications analyzed
- [ ] Security considerations addressed
- [ ] Accessibility compliance verified

---

## Review Process

### 1. Self-Review (Author)
```bash
# Use this checklist before requesting review
# Time: 15-30 minutes
# Focus: Structure, completeness, clarity
```

### 2. Peer Review (Technical)
```bash
# Technical accuracy and feasibility
# Time: 30-45 minutes
# Focus: Options analysis, implementation reality
```

### 3. ADHD Review (Accommodation Specialist)
```bash
# ADHD accommodation effectiveness
# Time: 15-30 minutes
# Focus: Cognitive load, user experience impact
```

### 4. Integration Review (Documentation)
```bash
# Consistency with existing architecture
# Time: 15-20 minutes
# Focus: Links, cross-references, terminology
```

---

## Automated Checks

### Linting Rules
- Consistent YAML front-matter
- Required sections present
- Link validation
- Terminology consistency (glossary compliance)
- ADHD metadata completeness

### Quality Metrics
- Reading level appropriate for audience
- Section length within cognitive load guidelines
- Visual structure (headers, bullets, tables) adequate
- Cross-reference coverage sufficient

---

## Common Issues & Solutions

### Frequent Problems
1. **Missing ADHD metadata** → Use template YAML front-matter
2. **Vague problem statements** → Start with one-sentence summary
3. **Insufficient option analysis** → Require minimum 2-3 alternatives
4. **Unclear consequences** → Separate positive, negative, neutral impacts
5. **Missing follow-up work** → Always include next steps

### Red Flags
- ❌ Single option presented as "analysis"
- ❌ No negative consequences acknowledged
- ❌ Unrealistic timeline or effort estimates
- ❌ Missing stakeholder input on user-facing changes
- ❌ No consideration of ADHD impact

### Quality Indicators
- ✅ Multiple viable options thoroughly analyzed
- ✅ Honest assessment of trade-offs and risks
- ✅ Clear implementation plan with success criteria
- ✅ Strong justification linked to business goals
- ✅ ADHD accommodations thoughtfully integrated

---

## LLM Review Prompt

*Use this prompt to have Claude or other LLMs review documentation:*

```
Please review this [RFC/ADR/arc42 section] against the Dopemux documentation standards:

1. Check structure and metadata completeness
2. Evaluate content quality and clarity
3. Assess ADHD accommodation considerations
4. Verify integration with existing documentation
5. Identify missing elements or quality issues
6. Suggest specific improvements

Focus on actionable feedback that improves decision quality and ADHD developer experience.
```

---

*Documentation Review Checklist v1.0 - Ensuring quality and ADHD accommodation in architectural documentation*