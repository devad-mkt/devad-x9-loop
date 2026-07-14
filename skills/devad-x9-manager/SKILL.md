---
name: devad-x9-manager
description: Use when an older Devad X9 prompt invokes devad-x9-manager, Top Manager, Sub Manager, Linx, Thinx, or Worker coordination and needs temporary v6 compatibility.
---

# Devad X9 Manager Compatibility

This name is a temporary v6 redirect.

Immediately load and follow `$devad-x9-loop`. Keep the requested role and old
prompt meaning, but use loop-lite task identity, exact claims, dispatch IDs,
direct callbacks, recovery snapshot, and all shared X9 safety gates.

Do not run a second manager flow from this shim.

Report once in durable state:
`COMPAT_REDIRECT:devad-x9-manager:devad-x9-loop`.

The old `.devad/manager/loop/` files are historical only. Removal of this shim
requires explicit owner approval in a later major version.
