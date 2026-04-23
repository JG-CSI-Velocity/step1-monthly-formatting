# ===========================================================================
# CORE-COMPETITION SHARED BOOTSTRAP
# ===========================================================================
# Loaded by every 60-series cell via:
#   exec(open(<this_path>).read(), globals())
#
# Responsibilities:
#   - Ensure COMPETITOR_MERCHANTS / tag_competitors / normalize_competitor_name
#     are in globals (auto-load 01_competitor_config.py from disk if needed).
#   - Ensure combined_df is in globals (auto-load parquet cache if needed).
#   - Ensure competitor_txns is in globals (rebuild via tag_competitors).
#   - Build `core_txns`: competitor_txns with wallets + P2P filtered out,
#     BNPL retained. This is the frame every 60-series cell uses.
#   - Provide CATEGORY_PALETTE / GEN_COLORS fallbacks so visuals don't
#     crash if cell 06 hasn't run yet.
#
# Sets module-level name `_BOOT_OK` (bool) -- cells should check it before
# rendering.
# ===========================================================================

from pathlib import Path
import os as _os

_G = globals()
_BOOT_OK = True


def _comp_dir():
    try:
        here = Path(__file__).resolve().parent
        if (here / '01_competitor_config.py').exists():
            return here
    except NameError:
        pass
    here = Path.cwd()
    for cand in [here, *here.parents[:8]]:
        if (cand / '01_competitor_config.py').exists():
            return cand
        if (cand / 'competition' / '01_competitor_config.py').exists():
            return cand / 'competition'
        hits = list(cand.glob('**/01_competitor_config.py'))
        if hits:
            return hits[0].parent
    return here


def _ensure_config():
    if all(n in _G for n in ('COMPETITOR_MERCHANTS', 'tag_competitors',
                             'normalize_competitor_name')):
        return True
    cfg = _comp_dir() / '01_competitor_config.py'
    if not cfg.exists():
        print(f"    Missing config at {cfg} and not in globals. "
              f"Run competition/01_competitor_config.py first.")
        return False
    print(f"    (auto-loading {cfg.name})")
    exec(compile(cfg.read_text(), str(cfg), 'exec'), _G)
    return 'COMPETITOR_MERCHANTS' in _G


def _ensure_combined():
    if 'combined_df' in _G:
        return True
    try:
        import pandas as pd
    except ImportError:
        return False
    client_id = _os.environ.get('CLIENT_ID', '')
    if not client_id:
        print("    CLIENT_ID not set; cannot locate parquet cache. "
              "Run setup/txn_setup first.")
        return False
    hits = []
    here = _comp_dir()
    for parent in [here, *here.parents[:10]]:
        hits = list(parent.glob(f"**/{client_id}_combined_cache.parquet"))
        if hits:
            break
    for env_var in ('TXN_BASE', 'ARS_TXN_BASE'):
        base = _os.environ.get(env_var)
        if base and not hits:
            hits = list(Path(base).rglob(f"{client_id}_combined_cache.parquet"))
    cache = next((h for h in hits if h.exists()), None)
    if cache is None:
        print(f"    Missing combined_df and no parquet cache for CLIENT_ID={client_id}. "
              f"Run setup/txn_setup first.")
        return False
    print(f"    (auto-loading combined_df from {cache.name})")
    _G['combined_df'] = pd.read_parquet(cache)
    return True


def _ensure_comptxns():
    if 'competitor_txns' in _G:
        return True
    if 'combined_df' not in _G or 'tag_competitors' not in _G:
        return False
    _tagged = _G['tag_competitors'](_G['combined_df'],
                                    merchant_col='merchant_consolidated')
    _ct = _tagged[_tagged['competitor_category'].notna()].copy()
    _ct['competitor_match'] = (
        _ct['merchant_consolidated'].apply(_G['normalize_competitor_name'])
    )
    _G['competitor_txns'] = _ct
    print(f"    (rebuilt competitor_txns: {len(_ct):,} rows)")
    return True


_BOOT_OK &= _ensure_config()
_BOOT_OK &= _ensure_combined()
_BOOT_OK &= _ensure_comptxns()

if 'CATEGORY_PALETTE' not in _G:
    _G['CATEGORY_PALETTE'] = {
        'Big Nationals':        '#E63946',
        'Top 25 Fed District':  '#C0392B',
        'Credit Unions':        '#2EC4B6',
        'Local Banks':          '#264653',
        'Digital Banks':        '#FF9F1C',
        'Custom':               '#F4A261',
        'Bnpl':                 '#E76F51',
    }

if 'GEN_COLORS' not in _G:
    _G['GEN_COLORS'] = {
        'accent': '#E63946', 'info': '#2B6CB0', 'warning': '#C05621',
        'success': '#2F855A', 'dark_text': '#1A202C',
        'muted': '#718096', 'grid': '#DDDDDD',
    }

# ---------------------------------------------------------------------------
# Filter: the defining choice of the 60-series.
# EXCLUDE wallets + P2P. KEEP BNPL.
# ---------------------------------------------------------------------------
CORE_EXCLUDE_CATS = ('wallets', 'p2p')

if _BOOT_OK:
    _ct_full = _G['competitor_txns']
    core_txns = _ct_full[~_ct_full['competitor_category'].isin(CORE_EXCLUDE_CATS)].copy()
    _G['core_txns'] = core_txns
    _excl_txns = len(_ct_full) - len(core_txns)
    _excl_pct = (_excl_txns / max(len(_ct_full), 1)) * 100
    _G['CORE_EXCLUDED_TXNS'] = _excl_txns
    _G['CORE_EXCLUDED_PCT'] = _excl_pct
    _G['CORE_SCOPE_NOTE'] = (
        f"Excludes wallets + P2P ({_excl_txns:,} txns, {_excl_pct:.1f}% of "
        f"competitor activity). BNPL retained."
    )
else:
    _G['core_txns'] = None
    _G['CORE_EXCLUDED_TXNS'] = 0
    _G['CORE_EXCLUDED_PCT'] = 0.0
    _G['CORE_SCOPE_NOTE'] = "(bootstrap failed)"
