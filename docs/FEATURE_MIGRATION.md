# Feature Migration

features.registry.json is the machine authority. legacy.inventory.json was
generated from the exact v3 skills, scripts, templates, Markdown headings, and
retained invariants.

Status meanings:

| Status | Meaning |
| --- | --- |
| RETAINED | Same owner and purpose |
| MOVED | Preserved under a new path or owner |
| ADAPTED | Preserved and strengthened |
| NEW | Introduced by the current v6 package |
| RETIRED | Intentionally rejected with reason and replacement |

scripts/validate_suite.py fails when one legacy ID lacks exactly one
classification or a moved/adapted/retired item lacks replacement and reason.
