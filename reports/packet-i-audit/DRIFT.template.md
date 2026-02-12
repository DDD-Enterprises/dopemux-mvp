# Packet I-AUDIT Drift Report

**Contract drift between schema, docs, and code**

---

## Schema vs Migrations

### Differences Found
| Item | Schema.sql | Migrations | Status |
|------|------------|------------|--------|
| [field/constraint] | [value] | [value] | [OK/DRIFT] |

**Notes**:
- Path A Law: schema.sql is canonical, migrations must match
- Any drift here is a FAIL under Path A

---

## Schema vs Docs

### MCP Contract Drift
| Contract Field | Docs Claim | Schema Reality | Status |
|----------------|------------|----------------|--------|
| correction_type | [enum values] | [actual constraint] | [OK/DRIFT] |

**Example**:
- **Docs**: `correction_type: "update|retraction"`
- **Code**: Valid values are `{'summary', 'tags', 'category', 'outcome', 'retraction'}`
- **Schema**: No `correction_type` field (ephemeral, derives `promotion_rule`)
- **Status**: DRIFT (docs out of sync with code)

---

## Code vs Schema

### Field Mismatches
[List any fields used in code but missing in schema, or vice versa]

**Notes**:
- Ephemeral fields (not stored) are OK if documented
- Missing CHECK constraints for enums used in code = DRIFT

---

## Recommendations

1. **Immediate Fixes**:
   - [List critical drift requiring immediate correction]

2. **Advisory**:
   - [List minor drift that should be fixed but not blocking]

3. **Documentation Updates**:
   - [List docs needing updates to match reality]

---

## Resolution Checklist

- [ ] All schema.sql vs migration drift resolved
- [ ] MCP contract docs match code reality
- [ ] All enum constraints documented
- [ ] Ephemeral fields explicitly noted in docs
