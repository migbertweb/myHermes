# Product Register

Focus: dashboards, admin panels, app UI, tools.

## Anti-patterns
- Decorative motion causing motion sickness or attention loss.
- Low-contrast muted text on tinted surfaces.
- Cards nested inside cards.
- Pure black / pure gray in high-density text areas.
- Bounce/elastic easing.

## Priorities
- Density with breathing room: 4px/8px/12px spacing scale.
- Information hierarchy through weight + size, not color alone.
- Error/empty/loading states designed first-class.
- Semantic z-index: dropdown < sticky < modal-backdrop < modal < toast < tooltip.

## Checklist
- Body text >= 4.5:1 on its background.
- Large text (>= 18px or bold >= 14px) >= 3:1.
- Touch targets >= 44px.
- No arbitrary z-index like 999/9999.
- `@media (prefers-reduced-motion: reduce)` on every transition/animation.
