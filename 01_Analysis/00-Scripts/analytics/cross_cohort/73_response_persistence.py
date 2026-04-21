# ===========================================================================
# CROSS-COHORT 73 -- Response Persistence
# ===========================================================================
# Question: once a mailer gets a response from an account, does that
# account keep responding to future mailers?
#
# For each mailed account with at least one response, compute:
#   - Did they respond again in any LATER mail round?
#   - How many rounds later was their second response?
#
# Scope: accounts with n_mailed >= 2 (need at least two rounds to measure
# persistence).  Within that, split by ICS channel.
#
# Uses the ordered list of Resp columns from cross_cohort/01.
# ===========================================================================

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

if 'cross_df' not in dir() or 'CROSS_RESP_COLS' not in dir():
    print('    cross_df / CROSS_RESP_COLS not ready. Run cross_cohort/01 first.')
else:
    if 'GEN_COLORS' not in dir():
        GEN_COLORS = {'info': '#2B6CB0', 'success': '#2F855A',
                      'warning': '#C05621', 'dark_text': '#1A202C',
                      'muted': '#718096'}

    resp_cols = CROSS_RESP_COLS
    if len(resp_cols) < 2:
        print('    Need >= 2 Resp columns to measure persistence. Skipping.')
    else:
        scope = cross_df[cross_df['n_mailed'] >= 2].copy()

        if scope.empty:
            print('    No accounts mailed >=2 times. Skipping.')
        else:
            # Build response matrix (boolean: responded that round)
            # format_odd treats "NU 1-4" as not-a-response; mirror that.
            resp_mat = (
                scope[resp_cols].replace('NU 1-4', pd.NA).notna().to_numpy()
            )

            # For each row: index of FIRST response (or -1), and whether
            # any later response exists after it.
            any_resp = resp_mat.any(axis=1)
            first_resp_idx = np.where(any_resp, resp_mat.argmax(axis=1), -1)

            def _responded_again(r, i):
                if i < 0 or i + 1 >= resp_mat.shape[1]:
                    return False
                return bool(r[i + 1:].any())

            responded_again = np.array([
                _responded_again(resp_mat[i], first_resp_idx[i])
                for i in range(len(scope))
            ])

            # Rounds until second response (nan if no second response)
            def _rounds_to_second(r, i):
                if i < 0:
                    return np.nan
                tail = r[i + 1:]
                if not tail.any():
                    return np.nan
                return int(np.argmax(tail) + 1)  # 1 = very next round

            rounds_to_2nd = np.array([
                _rounds_to_second(resp_mat[i], first_resp_idx[i])
                for i in range(len(scope))
            ])

            scope['responded_again'] = responded_again
            scope['rounds_to_2nd'] = rounds_to_2nd
            scope['first_responder'] = any_resp

            # ------------------------------------------------------
            # Per channel: among first-time responders, % responding again
            # ------------------------------------------------------
            CHANNEL_ORDER = [c for c in ['REF', 'DM', 'ICS-Unknown', 'Non-ICS']
                             if c in scope['ics_channel'].unique()]
            rows = []
            for ch in CHANNEL_ORDER:
                sub = scope[scope['ics_channel'] == ch]
                n_mailed2 = len(sub)
                n_first = int(sub['first_responder'].sum())
                n_again = int(sub['responded_again'].sum())
                again_rate = (n_again / n_first * 100) if n_first else float('nan')
                med_rounds = float(np.nanmedian(sub.loc[sub['responded_again'], 'rounds_to_2nd']))\
                    if n_again else float('nan')
                rows.append({
                    'Channel': ch,
                    'Accounts mailed >=2': n_mailed2,
                    'First-time responders': n_first,
                    'Responded again': n_again,
                    'Again-rate': again_rate,
                    'Median rounds to 2nd response': med_rounds,
                })
            tbl = pd.DataFrame(rows)

            show = tbl.copy()
            show['Accounts mailed >=2'] = show['Accounts mailed >=2'].map('{:,}'.format)
            show['First-time responders'] = show['First-time responders'].map('{:,}'.format)
            show['Responded again'] = show['Responded again'].map('{:,}'.format)
            show['Again-rate'] = show['Again-rate'].map(lambda v: f'{v:.1f}%' if pd.notna(v) else '--')
            show['Median rounds to 2nd response'] = show['Median rounds to 2nd response'].map(
                lambda v: f'{v:.1f}' if pd.notna(v) else '--')
            try:
                display_formatted(show, 'ARS Response Persistence by Channel')  # noqa: F821
            except NameError:
                print('\n   ARS Response Persistence by Channel')
                print(show.to_string(index=False))

            # ------------------------------------------------------
            # Bar chart: Again-rate by channel
            # ------------------------------------------------------
            fig, ax = plt.subplots(figsize=(12, 6))
            palette = {'REF': GEN_COLORS['success'], 'DM': GEN_COLORS['warning'],
                       'ICS-Unknown': GEN_COLORS['muted'], 'Non-ICS': GEN_COLORS['info']}
            xs = tbl['Channel']
            ys = tbl['Again-rate']
            ax.bar(xs, ys, color=[palette.get(c, GEN_COLORS['muted']) for c in xs],
                   edgecolor='white')
            for i, (c, v) in enumerate(zip(xs, ys)):
                if pd.notna(v):
                    ax.text(i, v + 1, f'{v:.1f}%', ha='center', fontsize=11,
                            color=GEN_COLORS['dark_text'], fontweight='bold')
            ax.set_ylabel('% of first-time responders that respond again later')
            ax.set_title('Response Persistence  —  once they respond, do they respond again?',
                         fontsize=15, fontweight='bold', color=GEN_COLORS['dark_text'], pad=12)
            for s in ('top', 'right'):
                ax.spines[s].set_visible(False)
            fig.text(0.5, -0.01,
                     'Scope: accounts mailed >= 2 times.  "Again" = another response in any LATER round.',
                     ha='center', fontsize=10, color=GEN_COLORS['muted'], style='italic')
            plt.tight_layout()
            plt.savefig('cross_cohort_73_persistence.png', dpi=160, bbox_inches='tight')
            plt.show()
            plt.close(fig)
