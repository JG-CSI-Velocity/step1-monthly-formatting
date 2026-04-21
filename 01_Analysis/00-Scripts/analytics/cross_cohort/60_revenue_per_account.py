# ===========================================================================
# CROSS-COHORT 60 -- Revenue per Account (Interchange Proxy)
# ===========================================================================
# We don't see interchange in the ODD data, so we estimate revenue from
# card Spend using a single bank-configurable basis-points assumption.
# This lets us ballpark the $ story for ICS vs Non-ICS.
#
# Knobs (edit in place, safe defaults below):
#   INTERCHANGE_BPS = 120   # 1.20% of debit Spend as interchange (regulated
#                             debit average, post-Durbin).  Override to your
#                             bank's realized rate if known.
#   INCLUDE_ECOSYSTEM_CLOSED = False   # closed accounts excluded by default.
#
# Output:
#   1. Per-channel monthly Spend, swipe velocity, implied interchange $/mo.
#   2. Lifetime implied interchange $ per account (open..latest).
#   3. $/mo bar chart ICS-REF | ICS-DM | Non-ICS.
# ===========================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

INTERCHANGE_BPS = 120
INCLUDE_CLOSED = False

_required = ('cross_df', 'rewards_df', 'CROSS_SWIPE_COLS')
_missing = [n for n in _required if n not in dir()]
if _missing:
    print(f'    Missing: {_missing}. Run cross_cohort/01 first.')
else:
    if 'GEN_COLORS' not in dir():
        GEN_COLORS = {'info': '#2B6CB0', 'success': '#2F855A',
                      'warning': '#C05621', 'dark_text': '#1A202C',
                      'muted': '#718096', 'primary': '#2D3748'}

    acct_col = 'Acct Number' if 'Acct Number' in rewards_df.columns else ' Acct Number'
    _MONTH_MAP = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

    def _spend_key(col):
        tag = col.replace(' Spend', '').strip()
        try:
            return (2000 + int(tag[3:])) * 100 + _MONTH_MAP.get(tag[:3], 0)
        except Exception:
            return 999999

    spend_cols = sorted(
        [c for c in rewards_df.columns if c.endswith(' Spend')
         and not c.startswith('Total') and not c.startswith('last')
         and not c.startswith('Last')],
        key=_spend_key,
    )

    if not spend_cols:
        print('    No monthly Spend columns in rewards_df. Skipping.')
    else:
        # Build account-level revenue frame
        rev = rewards_df[[acct_col] + spend_cols].copy()
        rev.columns = ['acct_number'] + spend_cols
        rev['acct_number'] = rev['acct_number'].astype(str).str.strip()
        for c in spend_cols:
            rev[c] = pd.to_numeric(rev[c], errors='coerce').fillna(0)

        # Join ICS channel + open/close dates
        _cx = cross_df[['acct_number', 'is_ics', 'ics_channel', 'open_date']].copy()
        if 'Date Closed' in rewards_df.columns:
            _cl = rewards_df[[acct_col, 'Date Closed']].copy()
            _cl.columns = ['acct_number', 'date_closed']
            _cl['acct_number'] = _cl['acct_number'].astype(str).str.strip()
            _cl['date_closed'] = pd.to_datetime(_cl['date_closed'], errors='coerce')
            _cx = _cx.merge(_cl, on='acct_number', how='left')
        else:
            _cx['date_closed'] = pd.NaT

        rev = rev.merge(_cx, on='acct_number', how='left')
        rev['ics_channel'] = rev['ics_channel'].fillna('Non-ICS')

        if not INCLUDE_CLOSED:
            rev = rev[rev['date_closed'].isna()]

        # Lifetime interchange (sum across all Spend cols * bps)
        _bps = INTERCHANGE_BPS / 10000.0
        rev['lifetime_spend'] = rev[spend_cols].sum(axis=1)
        rev['lifetime_interchange'] = rev['lifetime_spend'] * _bps

        # Months-open count for per-month averages:
        # count columns whose month >= open_date
        def _col_ts(col):
            tag = col.replace(' Spend', '').strip()
            return pd.Timestamp(year=2000 + int(tag[3:]), month=_MONTH_MAP[tag[:3]], day=1)

        _col_ts_arr = np.array([_col_ts(c) for c in spend_cols]).astype('datetime64[ns]')
        _opened = rev['open_date'].values.astype('datetime64[ns]')
        # months_open per row = number of spend_cols whose month >= opened
        eligible = _col_ts_arr[None, :] >= _opened[:, None]
        rev['months_open_in_window'] = eligible.sum(axis=1).clip(min=1)

        rev['spend_per_mo'] = rev['lifetime_spend'] / rev['months_open_in_window']
        rev['interchange_per_mo'] = rev['lifetime_interchange'] / rev['months_open_in_window']

        # ----------------------------------------------------------
        # Per-channel rollup
        # ----------------------------------------------------------
        CHANNEL_ORDER = [c for c in ['REF', 'DM', 'ICS-Unknown', 'Non-ICS']
                         if c in rev['ics_channel'].unique()]
        roll = (
            rev.groupby('ics_channel')
            .agg(accounts=('acct_number', 'count'),
                 avg_spend_mo=('spend_per_mo', 'mean'),
                 avg_interchange_mo=('interchange_per_mo', 'mean'),
                 avg_lifetime_interchange=('lifetime_interchange', 'mean'),
                 total_interchange=('lifetime_interchange', 'sum'))
            .reindex(CHANNEL_ORDER)
            .reset_index()
        )

        # ----------------------------------------------------------
        # Bar chart: avg interchange $/mo by channel
        # ----------------------------------------------------------
        fig, axes = plt.subplots(1, 2, figsize=(18, 6.5))

        channels = roll['ics_channel'].tolist()
        palette = {'REF': GEN_COLORS['success'], 'DM': GEN_COLORS['warning'],
                   'ICS-Unknown': GEN_COLORS['muted'], 'Non-ICS': GEN_COLORS['info']}
        colors = [palette.get(c, GEN_COLORS['muted']) for c in channels]

        axes[0].bar(channels, roll['avg_interchange_mo'], color=colors, edgecolor='white')
        axes[0].set_ylabel(f'$ per account per month  (Spend * {INTERCHANGE_BPS} bps)')
        axes[0].set_title('Implied interchange per account per month',
                          fontsize=15, fontweight='bold', color=GEN_COLORS['dark_text'], pad=10)
        for i, v in enumerate(roll['avg_interchange_mo']):
            axes[0].text(i, v * 1.02, f'${v:,.2f}', ha='center', fontsize=11,
                         color=GEN_COLORS['dark_text'], fontweight='bold')
        for s in ('top', 'right'):
            axes[0].spines[s].set_visible(False)

        axes[1].bar(channels, roll['avg_lifetime_interchange'], color=colors, edgecolor='white')
        axes[1].set_ylabel('$ lifetime per account (open .. latest month)')
        axes[1].set_title('Implied lifetime interchange per account',
                          fontsize=15, fontweight='bold', color=GEN_COLORS['dark_text'], pad=10)
        for i, v in enumerate(roll['avg_lifetime_interchange']):
            axes[1].text(i, v * 1.02, f'${v:,.0f}', ha='center', fontsize=11,
                         color=GEN_COLORS['dark_text'], fontweight='bold')
        for s in ('top', 'right'):
            axes[1].spines[s].set_visible(False)

        fig.suptitle(f'Revenue Proxy by ICS Channel  ({INTERCHANGE_BPS} bps on Spend)',
                     fontsize=20, fontweight='bold',
                     color=GEN_COLORS['dark_text'], y=1.02)
        fig.text(0.5, 0.97,
                 f'Interchange is an ESTIMATE from card Spend * {INTERCHANGE_BPS}bps.  '
                 f'Closed accounts {"included" if INCLUDE_CLOSED else "excluded"}.  '
                 f'Lifetime = sum over open-to-latest window.',
                 ha='center', fontsize=11, color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.savefig('cross_cohort_60_revenue_per_acct.png', dpi=160, bbox_inches='tight')
        plt.show()
        plt.close(fig)

        # ----------------------------------------------------------
        # Print recap
        # ----------------------------------------------------------
        show = roll.copy()
        show['accounts'] = show['accounts'].map('{:,}'.format)
        show['avg_spend_mo'] = show['avg_spend_mo'].map('${:,.2f}'.format)
        show['avg_interchange_mo'] = show['avg_interchange_mo'].map('${:,.2f}'.format)
        show['avg_lifetime_interchange'] = show['avg_lifetime_interchange'].map('${:,.0f}'.format)
        show['total_interchange'] = show['total_interchange'].map('${:,.0f}'.format)
        show.columns = ['Channel', 'Accounts', 'Spend/mo', 'Interchange/mo',
                        'Lifetime interchange/acct', 'Total channel interchange']

        try:
            display_formatted(show, f'Revenue Proxy by ICS Channel  ({INTERCHANGE_BPS} bps)')  # noqa: F821
        except NameError:
            print(f'\n   Revenue Proxy by ICS Channel  ({INTERCHANGE_BPS} bps)')
            print(show.to_string(index=False))

        # Lift vs Non-ICS
        if 'Non-ICS' in roll['ics_channel'].values:
            non = roll[roll['ics_channel'] == 'Non-ICS'].iloc[0]
            print()
            for ch in channels:
                if ch == 'Non-ICS':
                    continue
                row = roll[roll['ics_channel'] == ch].iloc[0]
                lift_mo = row['avg_interchange_mo'] - non['avg_interchange_mo']
                lift_lt = row['avg_lifetime_interchange'] - non['avg_lifetime_interchange']
                print(f'    {ch:>12s}: +${lift_mo:,.2f}/mo  +${lift_lt:,.0f} lifetime per account vs Non-ICS')
