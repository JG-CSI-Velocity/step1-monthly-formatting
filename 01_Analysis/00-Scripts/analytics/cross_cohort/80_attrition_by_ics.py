# ===========================================================================
# CROSS-COHORT 80 -- Attrition Risk by ICS Channel
# ===========================================================================
# Reuses the existing attrition framework (attrition_txn/01 built
# attrition_df with risk_tier in {Growing, Stable, Declining, Dormant,
# Closed} plus RISK_ORDER / RISK_PALETTE globals).
#
# New here: slice those risk tiers by ICS channel, same visual pattern as
# attrition_txn/06_risk_by_demographics.py.
#
# Scope: every account in attrition_df that we can join to cross_df.
# Channel values:  REF, DM, ICS-Unknown, Non-ICS  (ordered that way so ICS
# flavors sit next to each other on the chart).
# ===========================================================================

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

_required = ('attrition_df', 'RISK_ORDER', 'RISK_PALETTE', 'cross_df')
_missing = [n for n in _required if n not in dir()]
if _missing:
    print(f'    Missing: {_missing}. Run attrition_txn/01 AND cross_cohort/01 first.')
else:
    if 'GEN_COLORS' not in dir():
        GEN_COLORS = {'info': '#2B6CB0', 'success': '#2F855A',
                      'warning': '#C05621', 'dark_text': '#1A202C',
                      'muted': '#718096'}

    # ------------------------------------------------------------------
    # 1. Join ics_channel onto attrition_df
    # ------------------------------------------------------------------
    _chan = cross_df[['acct_number', 'ics_channel', 'is_ics']].copy()
    _chan['acct_number'] = _chan['acct_number'].astype(str).str.strip()
    _ad = attrition_df.copy()
    _ad['account_number'] = _ad['account_number'].astype(str).str.strip()
    _ad = _ad.merge(_chan, left_on='account_number', right_on='acct_number', how='left')
    _ad['ics_channel'] = _ad['ics_channel'].fillna('Non-ICS')

    CHANNEL_ORDER = ['REF', 'DM', 'ICS-Unknown', 'Non-ICS']
    CHANNEL_ORDER = [c for c in CHANNEL_ORDER if c in _ad['ics_channel'].unique()]

    # ------------------------------------------------------------------
    # 2. Stacked risk-tier % by channel  (same pattern as attrition cell 06)
    # ------------------------------------------------------------------
    ct = (
        pd.crosstab(_ad['ics_channel'], _ad['risk_tier'], normalize='index')
        .reindex(index=CHANNEL_ORDER)
        .reindex(columns=[t for t in RISK_ORDER if t in _ad['risk_tier'].unique()],
                 fill_value=0)
        * 100
    )

    fig, axes = plt.subplots(1, 2, figsize=(18, 7))

    ct.plot(
        kind='barh', stacked=True, ax=axes[0],
        color=[RISK_PALETTE.get(t, GEN_COLORS['muted']) for t in ct.columns],
        edgecolor='white', linewidth=0.5,
    )
    axes[0].set_xlabel('% of accounts in channel')
    axes[0].set_ylabel('ICS channel')
    axes[0].set_title('Risk tier mix by ICS channel',
                      fontsize=15, fontweight='bold',
                      color=GEN_COLORS['dark_text'], pad=12)
    axes[0].legend_.remove()
    for s in ('top', 'right'):
        axes[0].spines[s].set_visible(False)

    # ------------------------------------------------------------------
    # 3. Headline metrics table (closure, at-risk, velocity, balance)
    # ------------------------------------------------------------------
    rows = []
    for ch in CHANNEL_ORDER:
        sub = _ad[_ad['ics_channel'] == ch]
        if len(sub) == 0:
            continue
        closed = (sub['risk_tier'] == 'Closed').mean() * 100
        at_risk = sub['risk_tier'].isin(['Declining', 'Dormant']).mean() * 100
        growing = (sub['risk_tier'] == 'Growing').mean() * 100
        rows.append({
            'Channel': ch,
            'Accounts': len(sub),
            'Closed %': closed,
            'At-risk %': at_risk,
            'Growing %': growing,
            'Avg spend velocity': sub['spend_velocity'].mean() if 'spend_velocity' in sub else float('nan'),
            'Avg balance': sub['avg_bal'].mean() if 'avg_bal' in sub.columns else float('nan'),
        })
    headline = pd.DataFrame(rows)

    # Render table as a second panel (simple matplotlib table so it lives
    # on the same figure and prints cleanly in the deck)
    axes[1].axis('off')
    tbl_data = headline.copy()
    tbl_data['Accounts'] = tbl_data['Accounts'].map('{:,}'.format)
    for c in ('Closed %', 'At-risk %', 'Growing %'):
        tbl_data[c] = tbl_data[c].map(lambda v: f'{v:.1f}%' if pd.notna(v) else '--')
    tbl_data['Avg spend velocity'] = tbl_data['Avg spend velocity'].map(
        lambda v: f'{v:.2f}x' if pd.notna(v) else '--')
    tbl_data['Avg balance'] = tbl_data['Avg balance'].map(
        lambda v: f'${v:,.0f}' if pd.notna(v) else '--')

    the_table = axes[1].table(
        cellText=tbl_data.values, colLabels=tbl_data.columns,
        loc='center', cellLoc='center',
    )
    the_table.auto_set_font_size(False)
    the_table.set_fontsize(11)
    the_table.scale(1, 1.6)
    for (row, col), cell in the_table.get_celld().items():
        if row == 0:
            cell.set_facecolor(GEN_COLORS['primary'] if 'primary' in GEN_COLORS else '#2D3748')
            cell.set_text_props(color='white', fontweight='bold')
    axes[1].set_title('Headline numbers', fontsize=15, fontweight='bold',
                      color=GEN_COLORS['dark_text'], pad=12)

    # Shared legend for stacked bars
    _legend = [plt.Rectangle((0, 0), 1, 1,
                             facecolor=RISK_PALETTE.get(t, GEN_COLORS['muted']),
                             edgecolor='white') for t in ct.columns]
    fig.legend(_legend, list(ct.columns), loc='lower center',
               ncol=len(ct.columns), fontsize=11, frameon=False,
               bbox_to_anchor=(0.5, -0.01))

    fig.suptitle('Attrition Risk by ICS Channel',
                 fontsize=22, fontweight='bold',
                 color=GEN_COLORS['dark_text'], y=1.03)
    fig.text(0.5, 0.99,
             'Risk tiers from attrition_txn/01.  At-risk = Declining + Dormant.  '
             'CAVEAT: Non-ICS pool spans many more years of originations, so absolute Closed % '
             'is elevated vs ICS (newer program, less time to have closed).',
             ha='center', fontsize=11, color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.savefig('cross_cohort_80_attrition_by_ics.png', dpi=160, bbox_inches='tight')
    plt.show()
    plt.close(fig)

    # ------------------------------------------------------------------
    # 4. One-line takeaway
    # ------------------------------------------------------------------
    if 'Non-ICS' in headline['Channel'].values and len(headline) > 1:
        non = headline[headline['Channel'] == 'Non-ICS'].iloc[0]
        for ch in CHANNEL_ORDER:
            if ch == 'Non-ICS':
                continue
            row = headline[headline['Channel'] == ch]
            if row.empty:
                continue
            row = row.iloc[0]
            print(f'    {ch:>12s}: closed {row["Closed %"]:.1f}%  at-risk {row["At-risk %"]:.1f}%  '
                  f'vs Non-ICS closed {non["Closed %"]:.1f}% / at-risk {non["At-risk %"]:.1f}%  '
                  f'(closed {row["Closed %"] - non["Closed %"]:+.1f}pp, '
                  f'at-risk {row["At-risk %"] - non["At-risk %"]:+.1f}pp)')
