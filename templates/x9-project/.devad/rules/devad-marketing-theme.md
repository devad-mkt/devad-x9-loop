# Devad Marketing Theme

Use for `/chat-offer`, compact marketing/offer pages, public pricing, checkout offer surfaces, CTA effects, and Core Theme v2 visual rules.

## Role Map

| Role | Use for | Effect |
|---|---|---|
| Register/signup primary | Hero/header/product account creation | Galaxy |
| Register/signup contextual | Short account prompt near FAQ/footer | Black register CTA |
| Explore/secondary | Learn more, filters, tabs, FAQ/category actions | Rotating border |
| Purchase | Stripe checkout, subscribe, buy plan, lifetime purchase | Chroma bottom |
| Final pricing jump | End-page scroll back to pricing | Glow rainbow pill |

## Rules

- Choose the action role before choosing a button effect.
- Purchase CTAs must stay visually strongest in pricing/checkout sections.
- Explore or diagnostic actions must not compete with purchase.
- Use semantic tokens and namespaced classes. Do not paste raw reference selectors into app code.
- Do not change checkout, entitlement, auth, footer, header, deployment, or bridge behavior unless explicitly requested.
- `/chat-offer` and compact offer pages use this pack, not the broader dashboard pack.
- Add reduced-motion fallbacks for animated effects.

## Proof

For visual/theme work, verify desktop/mobile, no clipped button text, no horizontal overflow, readable hover/focus/active/disabled states, correct CTA role, and no unintended header/footer changes.
