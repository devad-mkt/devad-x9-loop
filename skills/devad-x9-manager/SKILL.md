---
name: devad-x9-manager
description: Use when an older Devad X9 prompt invokes devad-x9-manager, Top Manager, Sub Manager, Linx, Thinx, or Worker coordination and needs temporary v5 compatibility.
---

# Devad X9 Manager Compatibility

This name is a temporary v5 redirect.

Immediately load and follow `$devad-x9-loop`. Keep the requested role and old
prompt meaning, but use v5 task-ID roles, dispatch IDs, receipts, event state,
and safety gates. Do not run a second manager flow from this shim.

Report once in durable state: `COMPAT_REDIRECT:devad-x9-manager:devad-x9-loop`.
Removal is forbidden before v6 and requires owner approval.
