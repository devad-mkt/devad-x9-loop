# Linx Handover State

**Status:** OFF | INVENTORY | PLAN_ONLY | REVIEW | ACTIVATED | BLOCKED
**Handover ID:** NONE
**Old Linx thread:** NONE
**New Linx thread:** NONE
**Execution authority:** NONE | OLD_LINX_STATUS_ONLY | NEW_LINX
**One execution authority:** PASS | BLOCKED
**Rule:** one execution authority

## HANDOVER_INVENTORY_REQUEST

**Mode:** STATUS_ONLY
**Coverage:** PENDING | PASS | PARTIAL | BLOCKED

| Worker/lane | Thread | Durable reply | Local work | What next | Must not |
| --- | --- | --- | --- | --- | --- |

## OWNER_SCOPE_MATRIX

| Requirement | Owner state | Current state | Local-only work | Proof | Next | Must not |
| --- | --- | --- | --- | --- | --- | --- |

## NEW_LINX_PLAN

**Path:** NONE
**SHA-256:** NONE
**Plan-only receipt:** PENDING

## OLD_LINX_FINAL_REVIEW

**Result:** PENDING | PASS | FAIL
**Coverage gaps:** NONE
**Contradictions requiring Thinx:** NONE

## LINX_ACTIVATION_OK

**Token:** NONE
**Handover SHA-256:** NONE
**Plan SHA-256:** NONE
**Old Linx retired:** NO

## Heartbeat

**Target:** NONE
**Cadence:** 19 minutes
**Max wakes:** 76
**Expires:** NONE
**Pass lock:** SKIP_ACTIVE_MANAGER_PASS
