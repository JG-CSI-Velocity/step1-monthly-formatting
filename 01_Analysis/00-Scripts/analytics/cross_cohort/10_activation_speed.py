# ===========================================================================
# CROSS-COHORT 10 -- Activation Speed (Time-to-First-Swipe)
# ===========================================================================
# Question: do ICS-acquired accounts start using their card faster?
#
# SCOPE (fixed -- old version's cohort-match alone wasn't enough):
#   Restrict to accounts opened on/after the first observable Swipes
#   month.  Accounts opened before the Swipes data started would show
#   TTFS = months-to-first-observable-swipe, which is ~30+ months for a
#   2020 account and inflates Non-ICS median TTFS for a bogus reason.
#
# TTFS definition: months between Date Opened (month-start) and the first
# monthly Swipes column where swipes > 0.  -1 = never swiped in window.
#
# Output:
#   1. Summary table: count, swiped/never, %-by-M1/M3/M6, median TTFS.
#   2. Histogram overlay ICS vs Non-ICS (months 0..12, plus "Never swiped").
# ===========================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

_required = ('cross_df', 'CROSS_SWIPE_COLS')
if not all(n in dir() for n in _required):
    print('    cross_df / swipe columns not ready. Run cross_cohort/01 first.')
else:
    if 'GEN_COLORS' not in dir():
        GEN_COLORS = {'info': '#2B6CB0', 'success': '#2F855A',
                      'warning': '#C05621', 'dark_text': '#1A202C',
                      'muted': '#718096'}

    _MONTH_MAP = {'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
                  'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12}

    def _tag_to_ts(col, suffix=' Swipes'):
        tag = col.replace(suffix, '').strip()
        return pd.Timestamp(year=2000 + int(tag[3:]), month=_MONTH_MAP[tag[:3]], day=1)

    _swipe_ts = np.array([_tag_to_ts(c) for c in CROSS_SWIPE_COLS])
    _first_swipe_month = pd.Timestamp(_swipe_ts[0])
    _last_swipe_month = pd.Timestamp(_swipe_ts[-1])

    # -----------------------------------------------------------------
    # Scope gate: opened inside observable Swipes window
    # -----------------------------------------------------------------
    _n0 = len(cross_df)
    _has_date = cross_df['open_date'].notna()
    _in_window = _has_date & (cross_df['open_date'] >= _first_swipe_month)
    scope = cross_df[_in_window].copy()
    _n1 = len(scope)

    print(f'    Scope filter:')
    print(f'      All cross_df rows                                  : {_n0:,}')
    print(f'      With known Date Opened AND opened on/after {_first_swipe_month.strftime("%b %Y")} : '
          f'{_n1:,}  (dropped {_n0 - _n1:,})')
    print()

    if len(scope) == 0:
        print('    Empty scope after filter. Skipping.')
    else:
        # -----------------------------------------------------------------
        # Vectorized TTFS
        # -----------------------------------------------------------------
        def _ttfs_stats(frame):
            if len(frame) == 0:
                return None
            sw = frame[CROSS_SWIPE_COLS].apply(pd.to_numeric, errors='coerce').fillna(0).to_numpy()
            opened = frame['open_date'].values.astype('datetime64[M]').astype('datetime64[ns]')
            month_ts = _swipe_ts.astype('datetime64[ns]')
            eligible = month_ts[None, :] >= opened[:, None]
            hit = eligible & (sw > 0)
            any_hit = hit.any(axis=1)
            first_idx = hit.argmax(axis=1)

            first_hit_ts = month_ts[first_idx]
            ttfs_months = np.where(
                any_hit,
                ((first_hit_ts.astype('datetime64[M]') - opened.astype('datetime64[M]'))
                 .astype('timedelta64[M]').astype(int)),
                -1,
            )
            return {
                'count': len(frame),
                'swiped': int(any_hit.sum()),
                'never': int((~any_hit).sum()),
                'ttfs': ttfs_months,
                'any_hit': any_hit,
            }

        ics_s = _ttfs_stats(scope[scope['is_ics']])
        non_s = _ttfs_stats(scope[~scope['is_ics']])

        def _by_m(stats, k):
            if stats is None or stats['count'] == 0:
                return float('nan')
            return float(((stats['ttfs'] >= 0) & (stats['ttfs'] <= k)).sum()) / stats['count']

        def _median(stats):
            if stats is None or stats['swiped'] == 0:
                return float('nan')
            return float(np.median(stats['ttfs'][stats['any_hit']]))

        # -----------------------------------------------------------------
        # Summary table
        # -----------------------------------------------------------------
        rows = [
            ('Accounts in scope',                    ics_s['count'], non_s['count']),
            ('Swiped at least once',                 ics_s['swiped'], non_s['swiped']),
            ('Never swiped in window',               ics_s['never'],  non_s['never']),
            ('% swiped by month 1',                  _by_m(ics_s, 0), _by_m(non_s, 0)),
            ('% swiped by month 3',                  _by_m(ics_s, 2), _by_m(non_s, 2)),
            ('% swiped by month 6',                  _by_m(ics_s, 5), _by_m(non_s, 5)),
            ('Median months to first swipe',         _median(ics_s),  _median(non_s)),
        ]

        def _fmt(v, kind):
            if v is None or (isinstance(v, float) and np.isnan(v)):
                return '--'
            if kind == 'pct':
                return f'{v * 100:.1f}%'
            if kind == 'count':
                return f'{int(v):,}'
            return f'{v:.1f}'

        kinds = ['count', 'count', 'count', 'pct', 'pct', 'pct', 'num']
        summary = pd.DataFrame(
            [(r[0], _fmt(r[1], k), _fmt(r[2], k)) for r, k in zip(rows, kinds)],
            columns=['Metric', 'ICS', 'Non-ICS'],
        )
        try:
            display_formatted(summary, 'Activation Speed  (data-window scoped)')  # noqa: F821
        except NameError:
            print('   Activation Speed  (data-window scoped, ICS vs Non-ICS)')
            print(summary.to_string(index=False))

        # -----------------------------------------------------------------
        # Histogram overlay
        # -----------------------------------------------------------------
        def _hist(stats, max_m=12):
            if stats is None:
                return np.zeros(max_m + 2)
            arr = stats['ttfs']
            counts = np.zeros(max_m + 2)
            for m in range(max_m + 1):
                counts[m] = int((arr == m).sum())
            counts[max_m + 1] = int(((arr > max_m) & (arr >= 0)).sum()) + int((arr == -1).sum())
            return counts

        max_m = 12
        ics_h = _hist(ics_s, max_m)
        non_h = _hist(non_s, max_m)
        labels = [str(i) for i in range(max_m + 1)] + [f'>{max_m} / never']

        ics_share = ics_h / max(ics_h.sum(), 1) * 100
        non_share = non_h / max(non_h.sum(), 1) * 100

        fig, ax = plt.subplots(figsize=(16, 8))
        x = np.arange(len(labels))
        w = 0.38
        ax.bar(x - w / 2, ics_share, w, label='ICS', color=GEN_COLORS['success'])
        ax.bar(x + w / 2, non_share, w, label='Non-ICS', color=GEN_COLORS['info'])

        ax.set_xticks(x)
        ax.set_xticklabels(labels, fontsize=14)
        ax.set_xlabel('Months from account open to first swipe',
                      fontsize=16, fontweight='bold')
        ax.set_ylabel('Share of cohort (%)', fontsize=16, fontweight='bold')
        ax.set_title('Activation Speed  —  ICS vs Non-ICS',
                     fontsize=22, fontweight='bold', color=GEN_COLORS['dark_text'], pad=14)
        ax.legend(frameon=False, fontsize=14)
        ax.tick_params(axis='both', labelsize=13)
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)

        fig.text(0.5, -0.01,
                 f'Scope: accounts opened on/after {_first_swipe_month.strftime("%b %Y")}.  '
                 f'N ICS={ics_s["count"]:,}  N Non-ICS={non_s["count"]:,}.',
                 ha='center', fontsize=13, color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.savefig('cross_cohort_10_ttfs.png', dpi=160, bbox_inches='tight')
        plt.show()
        plt.close(fig)

        _ics_m3 = _by_m(ics_s, 2)
        _non_m3 = _by_m(non_s, 2)
        if _ics_m3 == _ics_m3 and _non_m3 == _non_m3:
            faster = 'faster' if _ics_m3 > _non_m3 else 'slower'
            print(f'\n    Activation by month 3: ICS {_ics_m3 * 100:.1f}%   Non-ICS {_non_m3 * 100:.1f}%   '
                  f'({(_ics_m3 - _non_m3) * 100:+.1f}pp, ICS {faster})')
