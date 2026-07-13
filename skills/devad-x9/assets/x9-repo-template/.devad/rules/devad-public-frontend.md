# Devad Public Frontend

Use for public routes, marketing shell, docs, help, status, free tools, header/footer, SEO, performance, and public browser QA.

## Public Surface Rules

- Public pages use Laravel/Inertia/React through the shared marketing runtime. Do not create Blade public pages except the existing Inertia root shell.
- Keep dashboard/admin/authenticated runtime separate from public marketing runtime.
- Public marketing pages must not depend on SSR always being available; fallback hydration must resolve public pages.
- Public routes must not load dashboard/admin/editor chunks unless the page genuinely needs them.
- `/docs` is product docs; generated API/Scribe docs must not shadow it.
- `/free-tools/*` stays static. Do not convert free tools to Laravel controllers, Blade, Inertia, React, or iframes unless explicitly approved.
- Public headers/footer/nav must preserve approved product names: `SITE`, `POST`, `AI AGENT`, and `CHAT`.
- Public UI should be compact, scan-friendly, fast, and tokenized. Avoid nested cards, generic SaaS filler, clipped text, and horizontal overflow.

## Proof

For public shell/nav/layout work, verify desktop and mobile for relevant routes, no console/page errors, no body horizontal overflow, visible logo, one H1 where applicable, canonical/SEO when relevant, and exact public labels.
