# Barrier Co theme plan

Version: v1 (draft)

## Approval log
One row per approval. The scripts read this table: the first cell is the exact phrase, and a row without a date and an approver does not count. Only Jeet approves.

| Approval | Date | Approved by | Notes |
| --- | --- | --- | --- |
| Approved: design analysis | | | |
| Approved: tokens | | | |
| Approved: architecture | | | |
| Approved: data model | | | |
| Approved: seo | | | |
| Approved: prune | | | |
| Approved: asset pack <purpose> v<n> | | | |
| Approved: client design sign-off | | | Date the client signed off the design; changes after this are tickets |
| Approved: plan v1 | | | Phase 4 gate |
| Approved: release 1 | | | |

### Delegated authority
2026-10-01, Jeet: "you can plan everything and start developing. Create meta fields and meta objects as required. You can only push an unpublished theme. You cannot make it live. You cannot publish anything."

What this covers:
- Planning and building without stopping at each phase gate. Assumptions are logged under Open questions so they can be reviewed later.
- Creating metafield and metaobject definitions and entries on the store, each with a backup and a dry run first.

What stays forbidden:
- Publishing a theme, or pushing to the live theme.
- Publishing products, collections or pages to any sales channel.

`Approved: plan v1` and `Approved: release 1` are still Jeet's to write.

Not applicable to a new build (no existing store): export run, existing-inventory, migrate, seo push.

## Inputs
| Input | Status | Notes |
| --- | --- | --- |
| Project type | New build | Decided at kickoff 2026-10-01. No existing Shopify store, nothing to bring over |
| Base | Horizon 4.2.0, commit `f9aef27` | Merchant-facing build, default base (core rule 5). `upstream` = Shopify/horizon. Pruned after the build |
| Figma file and MCP access | Confirmed 2026-10-01 | [Design file](https://www.figma.com/design/oZ00gYRP11BAdFQYwo4fxj/BARRIER-CO-%7C%7C-DEV-READY--JEET--?node-id=965-1236&m=dev), jeet@isrcit.com, Full seat. No separate brand library. See tokens.md |
| Store | the-barrier-co.myshopify.com, alias `store`, role production | Custom app "Store Data Sync" installed 2026-10-01 with permanent token. Unpublished theme pushes only; no publishing (Delegated authority). No separate dev store |
| Fonts (supplied / missing) | Waiting | Files and licences, or looked up from the Figma text styles |
| Content sources | Waiting | Who writes the content; reviews or other content to bring in |
| Apps and integrations | Waiting | Apps the client already pays for; form, CRM or email platform |
| Brand assets | Waiting | Logo SVG, square mark for the favicon, share image |
| Launch date | Waiting | |
| Markets and languages | Waiting | |
| Existing store data | Export run 2026-10-01 | Read-only export to check for existing products and definitions before creating any |
| Tools | 1.6.2 | Installed by `setup_tools.sh` |

### Steps that apply (new build)
Figma links, fonts, launch app plan (new apps only), `/isrc:tokens` from Figma, Horizon base, `/isrc:import` for new content, `/isrc:assets`, `/isrc:seo` for new content, prune after build, full plan and approval gate. Not applicable: `/isrc:pull`, theme and data analysis, `/isrc:migrate`, visual regression against live.

## Design analysis
Link to the Phase 1 notes. Per page: ordered sections, elements, states, annotations (verbatim), mobile differences. Cross-page reuse map. Heading hierarchy per template.

## Tokens
Source of truth and why. Desktop breakpoint. Link to tokens.md and the alignment report.

## Architecture
Link to architecture.md. Summary of blocks, sections and snippets by type (curated, preset, one-off).

## Template map
| Template | Sections in order |
| --- | --- |

## Data model
Link to data-model.md and docs/data/import.xlsx. Open data decisions.

## SEO
Link to seo.md. Redirect count, canonical and noindex rules, JSON-LD types. New build: no crawl baseline; redirects only if a previous non-Shopify domain exists.

## Commitments
Performance budgets and page weight per template. Accessibility level. Devices: 1920, 1440, 1280, iPad (portrait and landscape), iPhone. Browsers.

## Build order
Foundation, then blocks in dependency order, then sections, then page assembly.

## Open questions and assumptions
| # | Question | Who answers | Answer or assumption | Status |
| --- | --- | --- | --- | --- |
| 1 | Figma design file, library file and prototype links | Client / designer | | Open |
| 2 | Brand font files and licences | Client | | Open |
| 3 | Launch date | Client | | Open |
| 4 | Markets and languages | Client | | Open |
| 5 | Apps the client already pays for; form, CRM or email platform | Client | | Open |
| 6 | Who writes the content | Client | | Open |
| 7 | Staging and production store handles | Jeet | the-barrier-co.myshopify.com | Answered |
| 8 | Any previous website or domain (redirects) | Client | | Open |
