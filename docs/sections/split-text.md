# split-text

## Ticket
From docs/architecture.md (split-text). Figma: 787:9003 / 787:9428 (mail-back collection program).
- Eyebrow and a large heading on the left, rich text on the right; stacked and centred on mobile.
- A paragraph that is only a link becomes the Tan uppercase "SEE LOCATIONS…" text link.

## Plan
- `sections/split-text.liquid`, CSS grid. No JS.
- Desktop: content column 1312 with a 38 end inset, so the text sits at Figma's 738–1338; the title column never gets narrower than its longest word.
- **Heading size**: H1 (60 / 32) or Display (70 / 48, the mail-back size).
- Eyebrow 16 desktop, 14 mobile; text 20 desktop, 16 mobile; link 15 ExtraBold.

## Reasoning
- **What:** a two-column text section.
- **Why:** intro-media has the same header but always adds media below; this needs text only.
- **Alternatives rejected:** intro-media with media turned off (would carry media settings that do nothing).
- **Impact:** the link styling is automatic, so merchants don't need a button block for it.
- **Approver:** Jeet (delegated).

## QA checklist
- [ ] 1440: heading at x 64, text 738–1338, heading 70 with Display.
- [ ] 1024: heading and text never overlap.
- [ ] 390: centred, heading 48 (Display), eyebrow 14, link on its own line in Tan.
- [ ] A paragraph with a link plus other words keeps the normal underlined link.

## Merchant guide
1. Type the eyebrow and heading (Enter for line breaks) and choose **Heading size**.
2. In the text, put a link on its own line to get the uppercase text-link style.
3. Use **Anchor** (for example `mail-back`) so other links can jump here.
