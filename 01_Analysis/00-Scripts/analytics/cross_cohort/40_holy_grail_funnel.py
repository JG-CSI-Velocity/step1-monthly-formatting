# ===========================================================================
# CROSS-COHORT 40 -- Holy-Grail Funnel  (data-floor scoped)
# ===========================================================================
# The one-slide story.  For ICS and Non-ICS separately, count:
#
#   Step 1: Opened        -- denominator for everything below
#   Step 2: Activated     -- any swipe in the first ACTIVATION_WINDOW_MONTHS
#                            months after open
#   Step 3: Mailed        -- ever received >=1 ARS offer
#   Step 4: Responded     -- responded to >=1 ARS offer
#   Step 5: Climbed >=1 tier
#
# SCOPE (why the previous version showed Non-ICS 6% -- bogus):
#   Our Swipes data only goes back to the first monthly Swipes column
#   (~Apr 2023).  Any account opened before that has no observable first
#   90 days, so it could never satisfy "activated within 3 months".  The
#   Non-ICS pool was dominated by those pre-data accounts, which dragged
#   the activation rate to 6%.
#
#   Fix: use a RELATIVE date floor -- include every account (ICS or
#   Non-ICS) whose Date Opened is within the observable Swipes window,
#   with at least ACTIVATION_WINDOW_MONTHS of follow-up still in the data.
#   No cohort-matching -- just the data floor.
#
# Closed accounts are included by default because the question "did this
# account activate in its first 3 months?" is answerable whether or not
# the account later closed.  Toggle with INCLUDE_CLOSED_ACCOUNTS below.
#
# Every filter prints how many accounts it drops so scope is auditable.
# ===========================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

ACTIVATION_WINDOW_MONTHS = 3
INCLUDE_CLOSED_ACCOUNTS = True

if 'cross_df' not in dir() or 'CROSS_SWIPE_COLS' not in dir():
    print('    cross_df / swipe columns not ready. Run cross_cohort/01 first.')
elif len(CROSS_SWIPE_COLS) < ACTIVATION_WINDOW_MONTHS + 1:
    print(f'    Need at least {ACTIVATION_WINDOW_MONTHS + 1} Swipes columns '
          f'to measure activation. Have {len(CROSS_SWIPE_COLS)}. Skipping.')
else:
    if 'GEN_COLORS' not in dir():
        GEN_COLORS = {'info': '#2B6CB0', 'success': '#2F855A',
                      'warning': '#C05621', 'dark_text': '#1A202C',
                      'muted': '#718096'}

    _MONTH_MAP = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

    def _swipe_col_to_ts(c):
        tag = c.replace(' Swipes', '').strip()
        return pd.Timestamp(year=2000 + int(tag[3:]), month=_MONTH_MAP[tag[:3]], day=1)

    _swipe_ts = np.array([_swipe_col_to_ts(c) for c in CROSS_SWIPE_COLS])
    _first_swipe_month = pd.Timestamp(_swipe_ts[0])
    _last_swipe_month = pd.Timestamp(_swipe_ts[-1])
    # Latest open_date that still has ACTIVATION_WINDOW_MONTHS of follow-up
    _max_open = _last_swipe_month - pd.offsets.MonthBegin(ACTIVATION_WINDOW_MONTHS - 1)

    print(f'    Swipes window      : {_first_swipe_month.date()} .. {_last_swipe_month.date()}  '
          f'({len(CROSS_SWIPE_COLS)} months)')
    print(f'    Open-date floor    : {_first_swipe_month.date()}  '
          f'(first observable month of Swipes data)')
    print(f'    Open-date ceiling  : {_max_open.date()}  '
          f'(needs {ACTIVATION_WINDOW_MONTHS} mo of follow-up)')
    print()

    # ------------------------------------------------------------------
    # Scope: open_date inside the observable window
    # ------------------------------------------------------------------
    _n0 = len(cross_df)
    s1 = cross_df[cross_df['open_date'].notna()].copy()
    _n1 = len(s1)
    scope = s1[(s1['open_date'] >= _first_swipe_month)
               & (s1['open_date'] <= _max_open)].copy()
    _n2 = len(scope)

    if not INCLUDE_CLOSED_ACCOUNTS and 'Date Closed' in cross_df.columns:
        scope = scope[scope['Date Closed'].isna() | pd.to_datetime(
            scope['Date Closed'], errors='coerce').isna()]
    _n3 = len(scope)

    print(f'    Scope filter:')
    print(f'      All cross_df rows                                      : {_n0:,}')
    print(f'      With a known Date Opened                               : {_n1:,}  '
          f'(dropped {_n0 - _n1:,})')
    print(f'      Opened inside observable Swipes window                 : {_n2:,}  '
          f'(dropped {_n1 - _n2:,})')
    if not INCLUDE_CLOSED_ACCOUNTS:
        print(f'      Still open (closed accounts excluded)                 : {_n3:,}  '
              f'(dropped {_n2 - _n3:,})')
    print()

    if len(scope) == 0:
        print('    Empty scope after filters. Cannot draw funnel.')
    else:
        # --------------------------------------------------------------
        # Step 2 -- activated within ACTIVATION_WINDOW_MONTHS
        # --------------------------------------------------------------
        def _activated_mask(frame):
            if len(frame) == 0:
                return np.zeros(0, dtype=bool)
            sw = frame[CROSS_SWIPE_COLS].apply(pd.to_numeric, errors='coerce').fillna(0).to_numpy()
            opened = frame['open_date'].values.astype('datetime64[ns]')
            opened_ms = opened.astype('datetime64[M]').astype('datetime64[ns]')
            month_ts = _swipe_ts.astype('datetime64[ns]')
            months_since_open = ((month_ts[None, :] - opened_ms[:, None])
                                 .astype('timedelta64[M]').astype(int))
            in_window = (months_since_open >= 0) & (months_since_open < ACTIVATION_WINDOW_MONTHS)
            return ((sw > 0) & in_window).any(axis=1)

        def _funnel(frame):
            activated = _activated_mask(frame)
            mailed = frame['ever_mailed'].to_numpy()
            responded = frame['ever_responded'].to_numpy() & mailed
            tier_up = (frame['tier_rank_delta'].fillna(0).to_numpy() > 0)
            return {
                'opened': len(frame),
                'activated': int(activated.sum()),
                'mailed': int(mailed.sum()),
                'responded': int(responded.sum()),
                'tier_up': int(tier_up.sum()),
            }

        ics_f = _funnel(scope[scope['is_ics']])
        non_f = _funnel(scope[~scope['is_ics']])

        steps = ['Opened',
                 f'Activated\n(<= {ACTIVATION_WINDOW_MONTHS} months)',
                 'Mailed\n(>=1 ARS offer)',
                 'Responded',
                 'Climbed\n>=1 tier']
        ics_vals = [ics_f['opened'], ics_f['activated'], ics_f['mailed'],
                    ics_f['responded'], ics_f['tier_up']]
        non_vals = [non_f['opened'], non_f['activated'], non_f['mailed'],
                    non_f['responded'], non_f['tier_up']]

        ics_pct = [v / ics_f['opened'] * 100 if ics_f['opened'] else 0 for v in ics_vals]
        non_pct = [v / non_f['opened'] * 100 if non_f['opened'] else 0 for v in non_vals]

        # --------------------------------------------------------------
        # Chart -- larger fonts across the board
        # --------------------------------------------------------------
        fig, axes = plt.subplots(1, 2, figsize=(20, 9), sharey=True)

        def _draw(ax, vals, pct, label, color):
            y = np.arange(len(steps))[::-1]
            width = np.array(pct) / 100.0
            ax.barh(y, width, color=color, alpha=0.88, edgecolor='white', linewidth=1.4)
            for i, (v, p) in enumerate(zip(vals, pct)):
                ax.text(min(width[i] + 0.012, 1.02), y[i],
                        f'{v:,}  ({p:.1f}%)',
                        va='center', ha='left',
                        fontsize=16, fontweight='bold',
                        color=GEN_COLORS['dark_text'])
            ax.set_yticks(y)
            ax.set_yticklabels(steps, fontsize=15, fontweight='bold')
            ax.set_xlim(0, 1.35)
            ax.set_xticks([0, 0.25, 0.5, 0.75, 1.0])
            ax.set_xticklabels(['0%', '25%', '50%', '75%', '100%'], fontsize=13)
            ax.set_xlabel('% of opened accounts in scope', fontsize=14)
            ax.set_title(label, fontsize=18, fontweight='bold',
                         color=GEN_COLORS['dark_text'], pad=14)
            for s in ('top', 'right'):
                ax.spines[s].set_visible(False)
            ax.tick_params(axis='both', labelsize=13)

        _draw(axes[0], ics_vals, ics_pct,
              f'ICS   (opened in scope: {ics_f["opened"]:,})', GEN_COLORS['success'])
        _draw(axes[1], non_vals, non_pct,
              f'Non-ICS   (opened in scope: {non_f["opened"]:,})', GEN_COLORS['info'])

        fig.suptitle('Holy-Grail Funnel: Open -> Activate -> Mail -> Respond -> Tier-Up',
                     fontsize=22, fontweight='bold',
                     color=GEN_COLORS['dark_text'], y=1.01)
        fig.text(0.5, -0.01,
                 f'Scope: accounts opened between '
                 f'{_first_swipe_month.strftime("%b %Y")} and '
                 f'{_max_open.strftime("%b %Y")}  '
                 f'({"closed accts included" if INCLUDE_CLOSED_ACCOUNTS else "still-open accts only"}).  '
                 f'Needs >= {ACTIVATION_WINDOW_MONTHS} months of follow-up.',
                 ha='center', fontsize=13, color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.savefig('cross_cohort_40_funnel.png', dpi=160, bbox_inches='tight')
        plt.show()
        plt.close(fig)

        # --------------------------------------------------------------
        # Step-to-step conversion print-out
        # --------------------------------------------------------------
        def _rel(curr, prev):
            return f'{curr / prev * 100:.1f}%' if prev else '--'

        print('    Step-to-step conversion (relative to previous step)')
        print(f'    {"Step":<22} {"ICS":>28} {"Non-ICS":>28}')
        print(f'    {"Opened":<22} {ics_f["opened"]:>28,} {non_f["opened"]:>28,}')
        print(f'    {"Activated":<22} '
              f'{(_rel(ics_f["activated"], ics_f["opened"]) + " of opened"):>28} '
              f'{(_rel(non_f["activated"], non_f["opened"]) + " of opened"):>28}')
        print(f'    {"Mailed":<22} '
              f'{(_rel(ics_f["mailed"], ics_f["activated"]) + " of activated"):>28} '
              f'{(_rel(non_f["mailed"], non_f["activated"]) + " of activated"):>28}')
        print(f'    {"Responded":<22} '
              f'{(_rel(ics_f["responded"], ics_f["mailed"]) + " of mailed"):>28} '
              f'{(_rel(non_f["responded"], non_f["mailed"]) + " of mailed"):>28}')
        print(f'    {"Climbed >=1 tier":<22} '
              f'{(_rel(ics_f["tier_up"], ics_f["responded"]) + " of responded"):>28} '
              f'{(_rel(non_f["tier_up"], non_f["responded"]) + " of responded"):>28}')
