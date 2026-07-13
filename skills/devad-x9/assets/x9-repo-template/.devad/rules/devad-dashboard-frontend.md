# Devad Dashboard Frontend

Use for authenticated dashboard, admin, sidebar, app tabs, workspace settings, tenant-controlled UI, and settings-aware behavior.

## Source First

- Use `rg` first for exact labels, hrefs, setting keys, owner functions, routes, guards, readers, and writers.
- Likely owners include `getNavSections`, `workspace-layout`, `settings-layout`, `navigation`, route files, controllers, policies, and shared props.
- CodeFlow can locate owners; Graphify can orient architecture; neither replaces exact source extraction.
- Browser/runtime evidence is required before claiming visible behavior when browser access is available.

## UI Authority

- Do not hardcode over admin, tenant, workspace, role, feature-flag, CMS, or runtime settings.
- Preserve existing data props, permissions, billing, workspace behavior, language, auth, notifications, Echo/Reverb setup, and middleware unless explicitly in scope.
- Dashboard shell changes are UI chrome unless the owner explicitly asks for feature behavior.
- Sidebar work must preserve real routes and settings. Disabled placeholders must show `Soon` and must not navigate.
- Superadmin/admin routes remain server-protected. Superadmin UI must not expose every customer workspace unless that path is explicitly intended.
- Workspace billing and app billing must not be mislabeled or silently merged.
- Dashboard tokens own authenticated surfaces. Do not let public marketing primitives or raw colors leak into dashboard controls.

## Proof

For dashboard/sidebar/settings changes, verify representative customer/admin pages, desktop/mobile, disabled links, duplicate settings sidebar absence, profile/workspace menu, and console errors when reachable.
