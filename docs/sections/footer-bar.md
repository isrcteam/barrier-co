# footer-bar

## Ticket
From docs/architecture.md (footer-bar). Figma: 787:9003 / 787:9428 (page foot).
- A slim Tan bar: "| BARRIER |" on the left and the policy links with the year on the right (stacked and centred on mobile).

## Plan
- `sections/footer-bar.liquid`, rendered in a `<footer>`. No JS.
- `[year]` in the text becomes the current year.
- The section sits flush under the section above (cancels the global section gap).

## Reasoning
- **What:** a minimal footer for landing pages that use the `landing` layout (no header or footer group).
- **Why:** the site footer group carries newsletter, menus and logos that the sustainability design leaves out.
- **Alternatives rejected:** the site footer with its sections hidden (hiding them in the group would hide them on every page).
- **Impact:** policy links are typed in the text, so they need updating if the policy URLs change.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] 1440: logotype left at x 64, links right, 13 caps.
- [ ] 390: stacked, centred, text 11.
- [ ] No gap between the section above and the bar.
- [ ] `[year]` shows the current year.

## Merchant guide
1. Type the policy links in **Text** and use `[year]` for the year.
2. Change the colours if the page background changes.
