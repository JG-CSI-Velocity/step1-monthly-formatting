# ===========================================================================
# CHURN BY SEGMENT: Who's Leaving? (Conference Edition)
# ===========================================================================
# Separate bar charts: churn/at-risk rate by engagement tier, PFI tier,
# age band, and account age band. Individual figures.

if 'retention_df' not in dir() or len(retention_df) == 0:
    print("    No retention data available. Skipping churn by segment.")
else:
    _at_risk_statuses = ['Declining', 'Cooling', 'Dormant', 'Closed']

    def _plot_churn_by(df, group_col, order, palette, title, subtitle):
        _grouped = df.groupby(group_col).agg(
            total=('acct_number', 'count'),
            at_risk=('health_status', lambda x: x.isin(_at_risk_statuses).sum()),
        ).reset_index()
        _grouped['at_risk_rate'] = _grouped['at_risk'] / _grouped['total'] * 100

        _valid_order = [o for o in order if o in _grouped[group_col].values]
        if len(_valid_order) == 0:
            _valid_order = _grouped[group_col].tolist()
        _grouped = _grouped.set_index(group_col).loc[_valid_order].reset_index()

        fig, ax = plt.subplots(figsize=(14, 7))
        x = range(len(_grouped))
        colors = [palette.get(t, GEN_COLORS['muted']) for t in _grouped[group_col]]

        bars = ax.bar(x, _grouped['at_risk_rate'], color=colors,
                      edgecolor='white', linewidth=0.5, width=0.5)

        for bar, (_, row) in zip(bars, _grouped.iterrows()):
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.5,
                    f"{row['at_risk_rate']:.1f}%\n({int(row['at_risk']):,} of {int(row['total']):,})",
                    ha='center', va='bottom', fontsize=14, fontweight='bold',
                    color=palette.get(row[group_col], GEN_COLORS['muted']))

        ax.set_xticks(x)
        ax.set_xticklabels(_grouped[group_col], fontsize=13, fontweight='bold')
        ax.set_ylabel("At-Risk Rate %", fontsize=16, fontweight='bold', labelpad=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_pct))

        gen_clean_axes(ax, keep_left=True, keep_bottom=True)
        ax.yaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)

        ax.set_title(title, fontsize=26, fontweight='bold',
                     color=GEN_COLORS['dark_text'], pad=35, loc='left')
        ax.text(0.0, 1.02, subtitle,
                transform=ax.transAxes, fontsize=16,
                color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.show()

    # Chart 1: By engagement tier
    if retention_df['engagement_tier'].nunique() > 1:
        _plot_churn_by(
            retention_df[retention_df['engagement_tier'] != 'Unknown'],
            'engagement_tier', ENGAGE_ORDER, ENGAGE_PALETTE,
            "At-Risk Rate by Engagement Tier",
            f"Declining + Cooling + Dormant + Closed  ({DATASET_LABEL})"
        )

    # Chart 2: By PFI tier
    if retention_df['pfi_tier'].nunique() > 1 and (retention_df['pfi_tier'] != 'Unknown').any():
        _pfi_order = ['Primary', 'Secondary', 'Tertiary', 'Incidental']
        _pfi_palette = {
            'Primary': GEN_COLORS['success'], 'Secondary': GEN_COLORS['info'],
            'Tertiary': GEN_COLORS['warning'], 'Incidental': GEN_COLORS['muted'],
        }
        _plot_churn_by(
            retention_df[retention_df['pfi_tier'] != 'Unknown'],
            'pfi_tier', _pfi_order, _pfi_palette,
            "At-Risk Rate by PFI Tier",
            f"Are peripheral members leaving faster?  ({DATASET_LABEL})"
        )

    # Chart 3: By age band
    if retention_df['age_band'].nunique() > 1 and (retention_df['age_band'] != 'Unknown').any():
        _plot_churn_by(
            retention_df[retention_df['age_band'] != 'Unknown'],
            'age_band', AGE_ORDER, AGE_PALETTE,
            "At-Risk Rate by Age Band",
            f"Which age groups are disengaging?  ({DATASET_LABEL})"
        )
