# ===========================================================================
# SEGMENT VS CAMPAIGN: Do Campaign Responders Upgrade More?
# ===========================================================================
# Cross-reference campaign response data with segment migration.
# Compare upgrade rates: responders vs non-responders.
# This is campaign ROI evidence.

if 'seg_evo_df' not in dir() or len(seg_evo_df) == 0:
    print("    No segment evolution data available. Skipping campaign cross-reference.")
else:
    try:
        # ------------------------------------------------------------------
        # 1. Identify campaign response columns
        # ------------------------------------------------------------------
        rewards_cols = [c.strip() for c in rewards_df.columns]
        resp_cols = sorted([c for c in rewards_cols if c.endswith(' Resp')])

        if len(resp_cols) == 0:
            print("    No campaign response columns found. Skipping.")
        else:
            # ------------------------------------------------------------------
            # 2. Flag accounts that responded to any campaign
            # ------------------------------------------------------------------
            acct_id_col = 'Acct Number'
            resp_data = rewards_df[[acct_id_col] + resp_cols].copy()
            resp_data[acct_id_col] = resp_data[acct_id_col].astype(str).str.strip()

            # Any non-null response = responded
            resp_data['any_response'] = resp_data[resp_cols].notna().any(axis=1)
            resp_data['response_count'] = resp_data[resp_cols].notna().sum(axis=1)

            # Merge into seg_evo_df
            seg_camp = seg_evo_df.merge(
                resp_data[[acct_id_col, 'any_response', 'response_count']],
                on=acct_id_col,
                how='left',
            )
            seg_camp['any_response'] = seg_camp['any_response'].fillna(False)
            seg_camp['response_count'] = seg_camp['response_count'].fillna(0)

            # Label groups
            seg_camp['camp_group'] = np.where(
                seg_camp['any_response'], 'Responder', 'Non-Responder'
            )

            # ------------------------------------------------------------------
            # 3. Compare upgrade rates
            # ------------------------------------------------------------------
            # Filter to accounts with valid direction
            valid = seg_camp[seg_camp['direction'].isin(
                ['upgraded', 'degraded', 'stable']
            )]

            if len(valid) == 0:
                print("    No accounts with valid migration direction. Skipping.")
            else:
                group_summary = valid.groupby('camp_group').agg(
                    total=('direction', 'count'),
                    upgraded=('direction', lambda x: (x == 'upgraded').sum()),
                    degraded=('direction', lambda x: (x == 'degraded').sum()),
                    stable=('direction', lambda x: (x == 'stable').sum()),
                ).reset_index()

                group_summary['upgrade_rate'] = (
                    group_summary['upgraded'] / group_summary['total'] * 100
                )
                group_summary['degrade_rate'] = (
                    group_summary['degraded'] / group_summary['total'] * 100
                )
                group_summary['stable_rate'] = (
                    group_summary['stable'] / group_summary['total'] * 100
                )

                # ------------------------------------------------------------------
                # 4. Grouped bar chart: upgrade/degrade/stable rates
                # ------------------------------------------------------------------
                fig, ax = plt.subplots(figsize=(16, 8))

                groups = group_summary['camp_group'].tolist()
                x = np.arange(len(groups))
                bar_width = 0.25

                bars_up = ax.bar(
                    x - bar_width, group_summary['upgrade_rate'],
                    width=bar_width, color=GEN_COLORS['success'],
                    edgecolor='white', linewidth=0.5, label='Upgraded'
                )
                bars_st = ax.bar(
                    x, group_summary['stable_rate'],
                    width=bar_width, color=GEN_COLORS['info'],
                    edgecolor='white', linewidth=0.5, label='Stable'
                )
                bars_dn = ax.bar(
                    x + bar_width, group_summary['degrade_rate'],
                    width=bar_width, color=GEN_COLORS['accent'],
                    edgecolor='white', linewidth=0.5, label='Degraded'
                )

                # Annotate bars
                for bars in [bars_up, bars_st, bars_dn]:
                    for bar in bars:
                        height = bar.get_height()
                        if height > 0:
                            ax.text(
                                bar.get_x() + bar.get_width() / 2,
                                height + 0.5,
                                f"{height:.1f}%",
                                ha='center', va='bottom',
                                fontsize=12, fontweight='bold',
                                color=GEN_COLORS['dark_text']
                            )

                ax.set_xticks(x)
                ax.set_xticklabels(groups, fontsize=15, fontweight='bold')
                ax.set_ylabel("% of Accounts", fontsize=16,
                              fontweight='bold', labelpad=10)
                ax.yaxis.set_major_formatter(
                    mticker.FuncFormatter(gen_fmt_pct)
                )

                gen_clean_axes(ax, keep_left=True, keep_bottom=True)
                ax.yaxis.grid(True, color=GEN_COLORS['grid'],
                              linewidth=0.5, alpha=0.7)
                ax.set_axisbelow(True)

                ax.legend(loc='upper right', fontsize=13, frameon=False)

                # Annotate account counts below x-axis labels
                for i, grp in enumerate(groups):
                    n = group_summary.loc[
                        group_summary['camp_group'] == grp, 'total'
                    ].values[0]
                    ax.text(i, -0.06, f"n={n:,}",
                            ha='center', va='top', fontsize=11,
                            color=GEN_COLORS['muted'], fontweight='bold',
                            transform=ax.get_xaxis_transform())

                ax.set_title(
                    "Campaign Responders vs. Non-Responders: Segment Migration",
                    fontsize=24, fontweight='bold',
                    color=GEN_COLORS['dark_text'], pad=35, loc='left'
                )
                ax.text(0.0, 1.02,
                        f"Do campaign responders upgrade segments more often?  "
                        f"({DATASET_LABEL})",
                        transform=ax.transAxes, fontsize=15,
                        color=GEN_COLORS['muted'], style='italic')

                plt.tight_layout()
                plt.show()

                # Highlight the finding
                resp_row = group_summary[
                    group_summary['camp_group'] == 'Responder'
                ]
                nonresp_row = group_summary[
                    group_summary['camp_group'] == 'Non-Responder'
                ]
                if len(resp_row) > 0 and len(nonresp_row) > 0:
                    r_up = resp_row['upgrade_rate'].values[0]
                    nr_up = nonresp_row['upgrade_rate'].values[0]
                    diff = r_up - nr_up
                    direction_word = "higher" if diff > 0 else "lower"
                    print(f"\n    Campaign responder upgrade rate: {r_up:.1f}%")
                    print(f"    Non-responder upgrade rate: {nr_up:.1f}%")
                    print(f"    Difference: {abs(diff):.1f}pp {direction_word} "
                          f"for responders")

    except (NameError, KeyError) as e:
        print(f"    Campaign cross-reference failed: {e}")
        print("    Skipping segment vs campaign analysis.")
