# ===========================================================================
# CROSS-COHORT 96 -- Composite Scorecard
# ===========================================================================
# One row per ICS channel (REF, DM, ICS-Unknown, Non-ICS).
# One column per KPI the deck actually needs:
#
#   Accounts                      | count
#   Activated by day 90           | % with first swipe within 90 days of open
#   Mailed (>=1 ARS offer)        | % of channel
#   Response rate (of mailed)     | % responded / mailed
#   Avg responses per mailed acct | mean
#   Climbed >=1 swipe tier        | %
#   Avg monthly Spend             | mean of MonthlySpend12 (if present)
#   Avg balance                   | mean Avg Bal (if present)
#   At-risk                       | % in attrition_df Declining+Dormant (if present)
#   Closed rate                   | % in attrition_df Closed (if present)
#
# Missing inputs are shown as '--' rather than crashing.
# ===========================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if 'cross_df' not in dir():
    print('    cross_df not available. Run cross_cohort/01 first.')
else:
    if 'GEN_COLORS' not in dir():
        GEN_COLORS = {'info': '#2B6CB0', 'success': '#2F855A',
                      'warning': '#C05621', 'dark_text': '#1A202C',
                      'muted': '#718096', 'primary': '#2D3748'}

    # ------------------------------------------------------------------
    # Optional joins -- attrition + balance/spend from rewards_df
    # ------------------------------------------------------------------
    _scope = cross_df.copy()

    if 'attrition_df' in dir():
        _ad = attrition_df[['account_number', 'risk_tier']].copy()
        _ad.columns = ['acct_number', 'risk_tier']
        _ad['acct_number'] = _ad['acct_number'].astype(str).str.strip()
        _scope = _scope.merge(_ad, on='acct_number', how='left')
    else:
        _scope['risk_tier'] = pd.NA

    if 'rewards_df' in dir():
        _acct_col = 'Acct Number' if 'Acct Number' in rewards_df.columns else ' Acct Number'
        _wanted = [_acct_col]
        for c in ('MonthlySpend12', 'Avg Bal'):
            if c in rewards_df.columns:
                _wanted.append(c)
        _rw = rewards_df[_wanted].copy()
        _rw = _rw.rename(columns={_acct_col: 'acct_number'})
        _rw['acct_number'] = _rw['acct_number'].astype(str).str.strip()
        for c in _wanted[1:]:
            _rw[c] = pd.to_numeric(_rw[c], errors='coerce')
        _scope = _scope.merge(_rw, on='acct_number', how='left')

    # Activation-by-90-days: use days_to_first_mail's SIBLING -- we have
    # CROSS_SWIPE_COLS from cell 01. Recompute lightly here.
    _MONTH_MAP = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}
    if 'CROSS_SWIPE_COLS' in dir() and CROSS_SWIPE_COLS:
        def _ts(c):
            t = c.replace(' Swipes', '').strip()
            return pd.Timestamp(year=2000 + int(t[3:]), month=_MONTH_MAP[t[:3]], day=1)
        _sw_ts = np.array([_ts(c) for c in CROSS_SWIPE_COLS]).astype('datetime64[ns]')
        _sw = _scope[CROSS_SWIPE_COLS].apply(pd.to_numeric, errors='coerce').fillna(0).to_numpy()
        _opened = _scope['open_date'].values.astype('datetime64[ns]')
        _deltas = (_sw_ts[None, :] - _opened[:, None]).astype('timedelta64[D]').astype(int)
        _within_90 = (_deltas >= 0) & (_deltas <= 90)
        _scope['_activated_90'] = ((_sw > 0) & _within_90).any(axis=1)
    else:
        _scope['_activated_90'] = False

    # ------------------------------------------------------------------
    # Per-channel row builder
    # ------------------------------------------------------------------
    CHANNEL_ORDER = [c for c in ['REF', 'DM', 'ICS-Unknown', 'Non-ICS']
                     if c in _scope['ics_channel'].unique()]

    def _pct(mask, denom_mask):
        d = int(denom_mask.sum())
        if d == 0:
            return float('nan')
        return int((mask & denom_mask).sum()) / d * 100

    def _mean(col, filt):
        s = _scope.loc[filt, col] if col in _scope.columns else None
        if s is None or len(s) == 0 or s.dropna().empty:
            return float('nan')
        return float(s.mean())

    rows = []
    for ch in CHANNEL_ORDER:
        m = _scope['ics_channel'] == ch
        rows.append({
            'Channel': ch,
            'Accounts': int(m.sum()),
            'Activated by day 90': _pct(_scope['_activated_90'], m),
            'Mailed (>=1 offer)': _pct(_scope['ever_mailed'], m),
            'Response rate': _pct(_scope['ever_responded'], m & _scope['ever_mailed']),
            'Avg responses / mailed': _mean('n_responded', m & _scope['ever_mailed']),
            'Climbed >=1 tier': _pct(_scope['tier_rank_delta'].fillna(0) > 0, m),
            'Avg monthly spend': _mean('MonthlySpend12', m),
            'Avg balance': _mean('Avg Bal', m),
            'At-risk (Decl+Dorm)': _pct(_scope['risk_tier'].isin(['Declining', 'Dormant']), m),
            'Closed': _pct(_scope['risk_tier'] == 'Closed', m),
        })
    score = pd.DataFrame(rows)

    # Formatting
    def _f_pct(v):
        return '--' if v != v else f'{v:.1f}%'

    def _f_num(v):
        return '--' if v != v else f'{v:.2f}'

    def _f_money(v):
        return '--' if v != v else f'${v:,.0f}'

    show = score.copy()
    show['Accounts'] = show['Accounts'].map('{:,}'.format)
    for c in ('Activated by day 90', 'Mailed (>=1 offer)', 'Response rate',
              'Climbed >=1 tier', 'At-risk (Decl+Dorm)', 'Closed'):
        show[c] = show[c].map(_f_pct)
    show['Avg responses / mailed'] = show['Avg responses / mailed'].map(_f_num)
    show['Avg monthly spend'] = show['Avg monthly spend'].map(_f_money)
    show['Avg balance'] = show['Avg balance'].map(_f_money)

    try:
        display_formatted(show, 'Composite Scorecard -- ICS Channel Performance')  # noqa: F821
    except NameError:
        print('\n   Composite Scorecard -- ICS Channel Performance')
        print(show.to_string(index=False))

    # ------------------------------------------------------------------
    # Render as a heat-styled matplotlib table for the deck
    # ------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(18, 2.2 + 0.55 * len(score)))
    ax.axis('off')

    tbl = ax.table(
        cellText=show.values, colLabels=show.columns,
        loc='center', cellLoc='center',
    )
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(10)
    tbl.scale(1, 1.7)

    # Header styling
    for col_i, _ in enumerate(show.columns):
        cell = tbl[0, col_i]
        cell.set_facecolor(GEN_COLORS['primary'])
        cell.set_text_props(color='white', fontweight='bold')

    # Channel column styling
    channel_colors = {'REF': '#E6FFFA', 'DM': '#FFFAF0',
                      'ICS-Unknown': '#F7FAFC', 'Non-ICS': '#EDF2F7'}
    for r_i, ch in enumerate(show['Channel'], start=1):
        for c_i in range(len(show.columns)):
            cell = tbl[r_i, c_i]
            cell.set_facecolor(channel_colors.get(ch, 'white'))

    ax.set_title('Composite Scorecard -- ICS Channel Performance',
                 fontsize=18, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=14, loc='left')
    fig.text(0.01, 0.01,
             'Denominators: "Response rate" is of mailed.  "Climbed >=1 tier" and'
             ' "At-risk"/"Closed" are of all accounts in the channel.  Missing data = "--".',
             fontsize=9.5, color=GEN_COLORS['muted'], style='italic')

    plt.savefig('cross_cohort_96_scorecard.png', dpi=160, bbox_inches='tight')
    plt.show()
    plt.close(fig)
