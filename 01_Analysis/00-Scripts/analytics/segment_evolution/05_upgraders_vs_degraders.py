# ===========================================================================
# UPGRADERS VS DEGRADERS: Comparative Profile Analysis
# ===========================================================================
# Side-by-side bar chart comparing demographics and financials
# for accounts that upgraded vs degraded segments.

if 'seg_evo_df' not in dir() or len(seg_evo_df) == 0:
    print("    No segment evolution data available. Skipping upgrader/degrader comparison.")
else:
    upgraders = seg_evo_df[seg_evo_df['direction'] == 'upgraded'].copy()
    degraders = seg_evo_df[seg_evo_df['direction'] == 'degraded'].copy()

    if len(upgraders) == 0 and len(degraders) == 0:
        print("    No upgraders or degraders found. Skipping comparison.")
    else:
        # ------------------------------------------------------------------
        # Build comparison metrics
        # ------------------------------------------------------------------
        metrics = []

        # Age
        if 'Account Holder Age' in seg_evo_df.columns:
            up_age = upgraders['Account Holder Age'].median()
            dn_age = degraders['Account Holder Age'].median()
            if pd.notna(up_age) or pd.notna(dn_age):
                metrics.append({
                    'metric': 'Median Age',
                    'upgraded': up_age if pd.notna(up_age) else 0,
                    'degraded': dn_age if pd.notna(dn_age) else 0,
                    'fmt': '{:.0f}',
                })

        # Average Balance
        if 'Avg Bal' in seg_evo_df.columns:
            up_bal = upgraders['Avg Bal'].median()
            dn_bal = degraders['Avg Bal'].median()
            if pd.notna(up_bal) or pd.notna(dn_bal):
                metrics.append({
                    'metric': 'Median Avg Balance',
                    'upgraded': up_bal if pd.notna(up_bal) else 0,
                    'degraded': dn_bal if pd.notna(dn_bal) else 0,
                    'fmt': '${:,.0f}',
                })

        # Current Balance
        if 'Curr Bal' in seg_evo_df.columns:
            up_curr = upgraders['Curr Bal'].median()
            dn_curr = degraders['Curr Bal'].median()
            if pd.notna(up_curr) or pd.notna(dn_curr):
                metrics.append({
                    'metric': 'Median Curr Balance',
                    'upgraded': up_curr if pd.notna(up_curr) else 0,
                    'degraded': dn_curr if pd.notna(dn_curr) else 0,
                    'fmt': '${:,.0f}',
                })

        # Waves present (data completeness)
        up_waves = upgraders['waves_present'].median()
        dn_waves = degraders['waves_present'].median()
        metrics.append({
            'metric': 'Median Waves Present',
            'upgraded': up_waves if pd.notna(up_waves) else 0,
            'degraded': dn_waves if pd.notna(dn_waves) else 0,
            'fmt': '{:.1f}',
        })

        # Product diversity (unique product codes)
        if 'Prod Code' in seg_evo_df.columns:
            up_prods = upgraders['Prod Code'].nunique()
            dn_prods = degraders['Prod Code'].nunique()
            metrics.append({
                'metric': 'Unique Products',
                'upgraded': up_prods,
                'degraded': dn_prods,
                'fmt': '{:.0f}',
            })

        # Account count
        metrics.append({
            'metric': 'Account Count',
            'upgraded': len(upgraders),
            'degraded': len(degraders),
            'fmt': '{:,.0f}',
        })

        if len(metrics) == 0:
            print("    Insufficient data for upgrader/degrader comparison.")
        else:
            # ------------------------------------------------------------------
            # Side-by-side bar chart
            # ------------------------------------------------------------------
            metric_names = [m['metric'] for m in metrics]
            up_vals = [m['upgraded'] for m in metrics]
            dn_vals = [m['degraded'] for m in metrics]

            # Normalize for display (each metric scaled 0-100 for visual comparison)
            max_vals = [max(abs(u), abs(d), 1) for u, d in zip(up_vals, dn_vals)]
            up_norm = [u / m * 100 for u, m in zip(up_vals, max_vals)]
            dn_norm = [d / m * 100 for d, m in zip(dn_vals, max_vals)]

            fig, ax = plt.subplots(figsize=(16, 8))

            y = np.arange(len(metric_names))
            bar_height = 0.35

            bars_up = ax.barh(y - bar_height / 2, up_norm,
                              height=bar_height, color=GEN_COLORS['success'],
                              edgecolor='white', linewidth=0.5,
                              label='Upgraded')
            bars_dn = ax.barh(y + bar_height / 2, dn_norm,
                              height=bar_height, color=GEN_COLORS['accent'],
                              edgecolor='white', linewidth=0.5,
                              label='Degraded')

            # Annotate with actual values
            for i, m in enumerate(metrics):
                fmt = m['fmt']
                ax.text(up_norm[i] + 1.5, i - bar_height / 2,
                        fmt.format(m['upgraded']),
                        va='center', ha='left', fontsize=12,
                        fontweight='bold', color=GEN_COLORS['success'])
                ax.text(dn_norm[i] + 1.5, i + bar_height / 2,
                        fmt.format(m['degraded']),
                        va='center', ha='left', fontsize=12,
                        fontweight='bold', color=GEN_COLORS['accent'])

            ax.set_yticks(y)
            ax.set_yticklabels(metric_names, fontsize=14, fontweight='bold')
            ax.set_xlabel("Relative Scale (% of max)", fontsize=14,
                          fontweight='bold', labelpad=10)

            gen_clean_axes(ax, keep_left=True, keep_bottom=True)
            ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5,
                          alpha=0.7)
            ax.set_axisbelow(True)
            ax.set_xlim(0, 120)

            ax.legend(loc='lower right', fontsize=14, frameon=False)

            ax.set_title("Upgrader vs. Degrader Profile Comparison",
                         fontsize=26, fontweight='bold',
                         color=GEN_COLORS['dark_text'], pad=35, loc='left')
            ax.text(0.0, 1.02,
                    f"How do accounts that improved differ from those that declined?  "
                    f"({DATASET_LABEL})",
                    transform=ax.transAxes, fontsize=15,
                    color=GEN_COLORS['muted'], style='italic')

            plt.tight_layout()
            plt.show()

            # Summary table
            print(f"\n    Upgraders: {len(upgraders):,} | "
                  f"Degraders: {len(degraders):,} | "
                  f"Ratio: {len(upgraders)/max(len(degraders),1):.2f}:1")
