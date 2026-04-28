# Audit Follow-Up Work — In Progress

**Date opened:** 2026-04-27
**Last updated:** 2026-04-28 (deck-mode plumbing landed; manifest validator added; cross_cohort audit complete)
**Owner:** JG

Single page tracking the two parallel branches spawned by the 2026-04-27 ARS pipeline audit. See `Analysis Audit 4-27.md` (repo root) for the underlying findings.

---

## Branch 1 — `fix/txn-denominator-injection`

**Status:** Pushed, awaiting PR + verification
**Remote:** https://github.com/JG-CSI-Velocity/ars-production-pipeline/tree/fix/txn-denominator-injection
**Last commit:** `baf984c fix(txn): inject eligible filter into TXN namespace`

### What it does

Wires the 4-denominator framework (defined in `pipeline/steps/subsets.py`) into the TXN script execution namespace. Before this fix, ~330 TXN scripts ran on raw `combined_df` / `rewards_df` and produced KPI cards labeled "Eligible Accounts" with a base that didn't match the ARS-side eligible count.

### Files changed

| File | Change |
|---|---|
| `01_Analysis/00-Scripts/analytics/txn_wrapper.py` | New `_inject_eligible_filter()` runs after `txn_setup`; filters `combined_df` and `rewards_df` to eligible accounts; exposes `ELIGIBLE_ACCOUNTS` set + `ELIGIBLE_FILTER_APPLIED` bool; preserves originals as `*_all` escape hatch |
| `01_Analysis/00-Scripts/analytics/campaign/04_campaign_penetration.py` | Labels switch between "Eligible portfolio" and "Total portfolio" based on `ELIGIBLE_FILTER_APPLIED`; comment, ylabel, funnel labels, table caption, console output all updated |

### Verification needed before merge

1. Run pipeline on a known client (one where prior decks exist).
2. Confirm `combined_df` row count drops to eligible-only (logged as before/after counts).
3. Confirm campaign KPI card "Eligible Accounts" matches ARS-side eligible count.
4. Spot-check 2-3 TXN slides for sane numbers.
5. Confirm no TXN section script crashes on missing data (filter no-ops gracefully when `ctx.subsets.eligible_data is None`).

### Known follow-ups (not in this PR)

- `general/02_portfolio_data.py:57` "Active Accounts" KPI — semantically correct after fix (combined_df is now eligible-only) but label could be sharper. Defer.
- `merchant/01_merchant_data.py:18-22` and `mcc_code/01_mcc_data.py:27-31` — `acct_pct` denominator now correct. Defer label review.
- Hardcoded `'TH-10'` / `'NU 5+'` campaign classifiers (`campaign/01:50-53`) — separate ticket, not denominator-related.
- `DEBIT_TYPES = ['SIG', 'PIN']` hardcoded in `general/02:13` — move to config in a separate PR.

---

## Branch 2 — `feature/client-deck-3-stories`

**Status:** Planning artifacts pushed; implementation pending
**Remote:** https://github.com/JG-CSI-Velocity/ars-production-pipeline/tree/feature/client-deck-3-stories
**Last commit:** `acb546b docs(deck): add 3-story client deck plan, slide manifest, and audit log`

### What it does

Compresses the current ~70-80 slide combined output into a focused **<40 slide** client-facing deck organized around three critical stories: ARS Performance, Competition, Financial Services Leakage. ICS section conditionally inserted when data present (32 slides without ICS / 38 with ICS).

### Artifacts shipped so far

| File | Purpose |
|---|---|
| `Analysis Audit 4-27.md` (repo root) | Living audit log. Entry 1 = denominator fix. Entry 2 = deck plan. Future entries appended. |
| `docs/deck/CLIENT_DECK_PLAN.md` | Full slide budget, narrative, compression rationale, open questions for JG/CSM |
| `docs/deck/slide_manifest.json` | Machine-readable manifest with 39 slide entries, module bindings, combine/filter rules, conditional sections |
| `docs/deck/validate_manifest.py` | Cross-checks every manifest module ID against `registry.py` and `txn_wrapper.TXN_SECTIONS`. Run before every commit that touches the manifest. |
| `01_Analysis/00-Scripts/pipeline/steps/deck_filter.py` | New step: filters `ctx.all_slides` per manifest in `client` / `supplementary` mode (no-op in `full` mode). Wired into `step_generate`. |
| `--deck-mode` CLI flag | Added to `01_Analysis/run.py`, choices: `full` (default) / `client` / `supplementary`. Plumbed through `client_config['deck_mode']` → `ARSContext.deck_mode`. |

### Implementation TODO (from `slide_manifest.json`)

**Done:**
- ~~Validate manifest module IDs match registered modules~~ → `docs/deck/validate_manifest.py`
- ~~Add `--mode=client` / `--mode=supplementary` flags~~ → `--deck-mode` in `run.py` + `deck_filter.py` step
- ~~Audit cross_cohort/~~ → 12 scripts catalogued in manifest under `cross_cohort_promotion_candidates`

**Remaining:**
1. **Track `source_script` in `AnalysisResult`** so deck filter can match per-script (currently per-section). Small change in `txn_wrapper._execute_scripts`.
2. **Build `analytics/executive/opportunity_stack.py`** (waterfall summing 4 story-level $ opportunities)
3. **Add filter support to `insights.conclusions`** (`filter='top3'|'ars'|'ics'|'competition'|'financial_services'`) so the four "So what" slides emit the right bullets per story.
4. **Implement conditional ICS insertion** (predicate: `ICS_cohort` produced any output → include slides 15-19, else skip)
5. **Promote cross_cohort scripts** flagged in `slide_manifest.json` `cross_cohort_promotion_candidates.promotion_recommended` (5 candidates).
6. **End-to-end pilot:** run `--deck-mode=client` against a real client. Verify slide count = 32 (no ICS) or 38 (with ICS). Side-by-side vs old ~70-slide deck.

**Estimated remaining effort:** ~1 day (down from 2 — foundational plumbing landed this session).

### Hard dependency

This branch **cannot be presented to a client until `fix/txn-denominator-injection` is merged.** Hero slides 5, 21, 27, 34 all consume cross-section numbers that depend on consistent ARS/TXN denominators.

---

## Recommended order of operations

1. **Today/tomorrow:** Open PR for `fix/txn-denominator-injection`. Run on a real client. Verify before/after numbers.
2. **After fix merges to main:** Rebase `feature/client-deck-3-stories` onto main. Begin implementation TODO 1-7.
3. **First pilot:** Run new `--mode=client` against the same client used for fix verification. Compare side-by-side with the old ~70-slide deck. Get CSM reaction before generalizing.
4. **Communicate:** Brief CSMs on the new deck structure once it's stable.
