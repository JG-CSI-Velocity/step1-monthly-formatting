# ===========================================================================
# CROSS-COHORT 71 -- Mailer Saturation Curve
# ===========================================================================
# Does the 2nd mailer earn its keep?  The 3rd?  The 5th?
#
# For each mailer number N (1..max offers sent), compute the response
# rate of accounts at exactly that N-offer level: p(responded to >=1 | N
# offers received).  Stratified by ICS channel so we can see if ICS
# accounts have a flatter or steeper saturation curve.
#
# Scope: accounts with n_mailed >= 1.  never-mailed accounts can't be on
# this chart (they have no saturation to measure).
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

    mailed = cross_df[cross_df['ever_mailed']].copy()

    if mailed.empty:
        print('    No mailed accounts. Skipping.')
    else:
        MIN_CELL_N = 30  # suppress points with too little data
        max_offers = int(mailed['n_mailed'].max())
        offers_range = list(range(1, max_offers + 1))

        # Three series: REF, DM, Non-ICS (plus 'ICS-Unknown' if meaningful)
        channel_order = [c for c in ['REF', 'DM', 'ICS-Unknown', 'Non-ICS']
                         if c in mailed['ics_channel'].unique()]

        curves = {}  # channel -> list of (n_offers, resp_rate or NaN, cell_n)
        for ch in channel_order:
            sub = mailed[mailed['ics_channel'] == ch]
            points = []
            for k in offers_range:
                cell = sub[sub['n_mailed'] == k]
                n = len(cell)
                if n < MIN_CELL_N:
                    points.append((k, float('nan'), n))
                else:
                    resp = cell['ever_responded'].mean() * 100
                    points.append((k, resp, n))
            curves[ch] = points

        # ---------------- chart ----------------
        fig, ax = plt.subplots(figsize=(14, 6.5))

        palette = {'REF': GEN_COLORS['success'], 'DM': GEN_COLORS['warning'],
                   'ICS-Unknown': GEN_COLORS['muted'], 'Non-ICS': GEN_COLORS['info']}

        for ch in channel_order:
            pts = curves[ch]
            xs = [p[0] for p in pts if not np.isnan(p[1])]
            ys = [p[1] for p in pts if not np.isnan(p[1])]
            ns = [p[2] for p in pts if not np.isnan(p[1])]
            ax.plot(xs, ys, marker='o', linewidth=2.2, color=palette.get(ch, GEN_COLORS['muted']),
                    label=f'{ch}  (N={sum(ns):,})')
            for x, y, n in zip(xs, ys, ns):
                ax.text(x, y + 1, f'n={n:,}', ha='center', fontsize=8.5,
                        color=palette.get(ch, GEN_COLORS['muted']), alpha=0.85)

        ax.set_xticks(offers_range)
        ax.set_xlabel('Number of ARS offers the account has received')
        ax.set_ylabel('Response rate  (% responded to >=1 offer)')
        ax.set_title('Mailer Saturation: Response Rate vs # of Offers',
                     fontsize=16, fontweight='bold', color=GEN_COLORS['dark_text'], pad=12)
        ax.legend(frameon=False, loc='lower right')
        for s in ('top', 'right'):
            ax.spines[s].set_visible(False)

        fig.text(0.5, -0.01,
                 f'Scope: accounts mailed >= 1.  Points with fewer than {MIN_CELL_N} accounts suppressed.',
                 ha='center', fontsize=10, color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.savefig('cross_cohort_71_saturation.png', dpi=160, bbox_inches='tight')
        plt.show()
        plt.close(fig)

        # ---------------- incremental response table ----------------
        # For each N, incremental response = responders_at_N - responders_at_N-1
        # (interpreted as: did going from N-1 to N mailings convert a non-responder)
        print('\n    Saturation deltas (incremental response rate at each Nth mailer):')
        for ch in channel_order:
            pts = curves[ch]
            prev = None
            print(f'      {ch}:')
            for k, rate, n in pts:
                if np.isnan(rate):
                    print(f'        mailer {k}: n={n:,}  (suppressed)')
                    continue
                if prev is None:
                    print(f'        mailer {k}: {rate:.1f}%   (baseline, n={n:,})')
                else:
                    delta = rate - prev
                    arrow = '+' if delta >= 0 else ''
                    print(f'        mailer {k}: {rate:.1f}%   {arrow}{delta:.1f}pp   (n={n:,})')
                prev = rate
