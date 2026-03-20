---
id: DOCUMENTATION_LOCATION_UPDATE
title: Documentation Location Update
type: explanation
owner: '@hu3mann'
author: '@hu3mann'
date: '2026-03-17'
last_review: '2026-03-17'
next_review: '2026-06-15'
prelude: Documentation Location Update (explanation) for dopemux documentation and
  developer workflows.
---
# Documentation Location Update

## Changes Made

### ✅ Moved Documentation to Skill Directory

**From**: `docs/pr_prep/*.md` (repo)
**To**: `/Users/hue/.gemini/skills/pr-prep-specialist/docs/` (skill)

**Files Moved**: 33 documentation files
- 31 policy/rule files
- `ARTIFACT_PLACEMENT_POLICY.md`
- `SKILL_MODEL.md`

### 📁 Current Correct Locations

**Documentation** (skill directory):
```
📁 /Users/hue/.gemini/skills/pr-prep-specialist/docs/
   ├── 31 policy/rule files (.md)
   ├── ARTIFACT_PLACEMENT_POLICY.md
   └── SKILL_MODEL.md
```

**Proof Artifacts** (repo proof directory):
```
📁 proof/pr_prep/
   ├── PROOF_BUNDLE_INDEX.json
   ├── TP-PRPS-000-SPECIFICATION-BUNDLE.json
   ├── TP-PRPS-008-000-MASTER-COMPREHENSIVE-BUNDLE.json
   ├── live_pilot_execution/
   │   └── TP-PRPS-008-LIVE-PILOT-COMPREHENSIVE-BUNDLE.json
   └── instructions/
       ├── VIBE_CHECKPOINT_VALIDATION.json
       └── VIBE_GUARDRAIL_MANIFEST.json
```

**Implementation** (repo src directory):
```
📁 src/dopemux_pr_prep_specialist/
   ├── __init__.py
   ├── cli.py
   ├── intake.py
   ├── audit.py
   ├── obligations.py
   ├── drafting.py
   ├── validation.py
   └── handoff.py
```

**Vibe Adapters** (repo docs directory):
```
📁 docs/pr_prep/adapters/vibe/
   ├── GUARDRAILS.md
   ├── CHECKPOINT_SEQUENCE.md
   ├── OPERATOR_REVIEW_FORM.md
   └── AGENT_TEMPLATE.md
```

### 🔒 Policy Compliance

**ARTIFACT_PLACEMENT_POLICY.md** updated to reflect:
- ✅ Documentation → Skill directory
- ✅ Proof artifacts → Repo proof directory
- ✅ Implementation → Repo src directory
- ✅ Vibe adapters → Repo docs directory

### 📋 Updated Verification Checklist

**Completed** ✅ (15/15)
- [x] Live pilot executed under GO_DRAFT_FIRST posture
- [x] Proof bundle generated (34 artifacts + 1 comprehensive)
- [x] All validation gates passed
- [x] No critical blockers found
- [x] Chain of custody documented
- [x] Multi-tool architecture fully specified
- [x] TP-PRPS-000 packet definition complete
- [x] Comprehensive proof bundle created
- [x] Vibe guardrails plan created
- [x] Vibe guardrails implemented
- [x] Checkpoint validation passed
- [x] Guardrail manifest created
- [x] Artifact placement corrected
- [x] **Documentation moved to skill directory** ✅ NEW
- [x] Placement policy updated

### 🎯 Rationale

**Why Documentation in Skill Directory**:
1. **Skill Portability**: Documentation travels with skill
2. **Version Alignment**: Docs match skill version
3. **Isolation**: Prevents repo documentation bloat
4. **Distribution**: Easier to package and distribute
5. **Maintenance**: Single location for skill documentation

**Why Proof in Repo**:
1. **Governance**: Proof stays with governance artifacts
2. **Audit Trail**: Repo maintains history
3. **CI/CD Access**: Pipeline can access proof
4. **Review**: Easier for operators to find
5. **Persistence**: Repo is long-term storage

### 🚀 Impact

**No Breaking Changes**:
- All proof bundles still in `proof/pr_prep/`
- All implementation still in `src/`
- Only documentation moved to skill directory
- All references updated in handoff summary

**Improved Organization**:
- Skill is self-contained
- Repo proof is easily accessible
- Clear separation of concerns
- Compliant with policy

### 📊 Current Status

**Workstream**: READY FOR OPERATOR REVIEW ✅
**Documentation**: MOVED TO SKILL DIRECTORY ✅
**Proof Artifacts**: IN REPO PROOF DIRECTORY ✅
**Vibe Guardrails**: IMPLEMENTED ✅
**Multi-Tool Architecture**: SPECIFICATION COMPLETE
**Live Pilot**: SUCCESS
**All outputs in single JSON format** 🚀
