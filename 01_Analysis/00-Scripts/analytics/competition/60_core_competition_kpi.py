# ===========================================================================
# CORE COMPETITION KPI (Ex Wallets + P2P, Keep BNPL) -- Conference Edition
# ===========================================================================
# Excludes digital wallets (Apple Pay, Venmo, PayPal, Cash App, ...) and P2P
# (Zelle). KEEPS BNPL (Affirm, Klarna, Afterpay) because BNPL balances
# substitute for credit-card / line-of-credit products.
#
# For a strict banks-only view (no BNPL either), filter core_txns further
# via BANK_CATEGORIES after the bootstrap.
# ===========================================================================

from pathlib import Path
from matplotlib.patches import FancyBboxPatch
import matplotlib.pyplot as plt


# ---------------------------------------------------------------------------
# Locate + exec the shared core-bootstrap that defines `core_txns`,
# `combined_df`, `CORE_SCOPE_NOTE`, `CORE_EXCLUDED_TXNS`, `_BOOT_OK`, etc.
# ---------------------------------------------------------------------------
def _load_core_bootstrap():
    try:
        here = Path(__file__).resolve().parent
    except NameError:
        here = Path.cwd()
    bp = here / '_core_bootstrap.py'
    if not bp.exists():
        for p in [here, *here.parents[:10]]:
            cand = p / '_core_bootstrap.py'
            if cand.exists():
                bp = cand; break
            cand = p / 'competition' / '_core_bootstrap.py'
            if cand.exists():
                bp = cand; break
            hits = list(p.glob('**/_core_bootstrap.py'))
            if hits:
                bp = hits[0]; break
    if not bp.exists():
        raise FileNotFoundError(
            "Cannot find _core_bootstrap.py. Place it next to this cell "
            "(competition/_core_bootstrap.py)."
        )
    exec(compile(bp.read_text(), str(bp), 'exec'), globals())


_load_core_bootstrap()

if not _BOOT_OK:
    print("    Skipping -- required inputs missing.")
else:
    total_trans = len(core_txns)
    total_accts = core_txns['primary_account_num'].nunique()
    total_comps = core_txns['competitor_match'].nunique()

    total_all_trans = len(combined_df)
    total_all_accts = combined_df['primary_account_num'].nunique()

    pct_trans = (total_trans / total_all_trans * 100) if total_all_trans else 0
    pct_accts = (total_accts / total_all_accts * 100) if total_all_accts else 0

    bnpl = core_txns[core_txns['competitor_category'] == 'bnpl']
    bnpl_accts = bnpl['primary_account_num'].nunique()
    bnpl_pct = (bnpl_accts / max(total_all_accts, 1)) * 100

    kpis = [
        (f"{pct_accts:.1f}%", "of Accounts\nUsing Bank + BNPL Competitors", GEN_COLORS['accent']),
        (f"{pct_trans:.1f}%", "of Transactions\nto Bank + BNPL Competitors", GEN_COLORS['info']),
        (f"{total_comps}",    "Distinct Competitors\nDetected",              GEN_COLORS['warning']),
        (f"{bnpl_pct:.1f}%",  "of Accounts\nCarrying BNPL Balances",         GEN_COLORS['success']),
    ]

    fig, axes = plt.subplots(1, 4, figsize=(22, 6))
    fig.patch.set_facecolor('#FFFFFF')
    for ax, (value, label, color) in zip(axes, kpis):
        ax.set_xlim(0, 1); ax.set_ylim(0, 1); ax.axis('off')
        ax.add_patch(FancyBboxPatch(
            (0.03, 0.05), 0.94, 0.90, boxstyle="round,pad=0.05",
            facecolor=color, alpha=0.08, edgecolor=color, linewidth=2.8,
        ))
        ax.text(0.5, 0.62, value, transform=ax.transAxes,
                fontsize=54, fontweight='bold', color=color,
                ha='center', va='center')
        ax.text(0.5, 0.20, label, transform=ax.transAxes,
                fontsize=16, fontweight='bold', color=GEN_COLORS['dark_text'],
                ha='center', va='center', linespacing=1.4)

    fig.suptitle("Core Competitive Exposure — Banks + BNPL",
                 fontsize=30, fontweight='bold',
                 color=GEN_COLORS['dark_text'], y=1.04)
    fig.text(0.5, 0.97, CORE_SCOPE_NOTE,
             ha='center', fontsize=14, color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.savefig('competition_60_core_kpi.png', dpi=160, bbox_inches='tight')
    plt.show()
    plt.close(fig)

    if pct_accts < 25:
        print(f"\n    OPPORTUNITY: Only {pct_accts:.1f}% of accounts show "
              f"bank + BNPL competitor activity.")
    elif pct_accts > 45:
        print(f"\n    WARNING: {pct_accts:.1f}% of accounts show bank + BNPL "
              f"competitor activity. Significant displacement risk.")
