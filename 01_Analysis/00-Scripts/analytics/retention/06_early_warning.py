# ===========================================================================
# EARLY WARNING: At-Risk Account Identification (Conference Edition)
# ===========================================================================
# Scatter plot: spend trajectory (slope) vs current spend level.
# Red zone = high-value accounts with steep decline. (14,7).

if 'retention_df' not in dir() or len(retention_df) == 0:
    print("    No retention data available. Skipping early warning chart.")
else:
    _at_risk = retention_df[retention_df['health_status'].isin(['Declining', 'Cooling', 'Dormant'])].copy()

    if len(_at_risk) == 0:
        print("    No at-risk accounts identified. Skipping early warning chart.")
    else:
        # Count warning signals per account
        _at_risk['warning_signals'] = 0

        # Signal 1: Negative spend slope
        _at_risk.loc[_at_risk['spend_slope'] < -5, 'warning_signals'] += 1

        # Signal 2: Consecutive zero months
        _at_risk.loc[_at_risk['consecutive_zero_months'] >= 2, 'warning_signals'] += 1

        # Signal 3: High prior spend now dropped
        _at_risk.loc[
            (_at_risk['prior_3mo_avg_spend'] > _at_risk['prior_3mo_avg_spend'].median()) &
            (_at_risk['last_3mo_avg_spend'] < _at_risk['prior_3mo_avg_spend'] * 0.3),
            'warning_signals'
        ] += 1

        # Signal 4: Was in higher engagement tier (if available)
        if 'engagement_tier' in _at_risk.columns:
            _at_risk.loc[
                _at_risk['engagement_tier'].isin(['Power', 'Heavy']),
                'warning_signals'
            ] += 1

        fig, ax = plt.subplots(figsize=(14, 7))

        # Plot all at-risk accounts
        _colors = _at_risk['warning_signals'].map({
            0: GEN_COLORS['muted'],
            1: GEN_COLORS['warning'],
            2: '#F4A261',
            3: GEN_COLORS['accent'],
            4: GEN_COLORS['accent'],
        }).fillna(GEN_COLORS['muted'])

        _sizes = _at_risk['prior_3mo_avg_spend'].clip(lower=0).apply(
            lambda v: max(10, min(200, v / 5))
        )

        ax.scatter(
            _at_risk['spend_slope'],
            _at_risk['prior_3mo_avg_spend'],
            c=_colors, s=_sizes, alpha=0.5, edgecolors='white', linewidth=0.3
        )

        ax.set_xlabel("Spend Trajectory (slope, last 6 months)", fontsize=16, fontweight='bold')
        ax.set_ylabel("Prior 3-Month Avg Spend", fontsize=16, fontweight='bold')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_dollar))

        gen_clean_axes(ax, keep_left=True, keep_bottom=True)
        ax.yaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
        ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)

        # Highlight danger zone (high spend + steep decline)
        _median_spend = _at_risk['prior_3mo_avg_spend'].median()
        ax.axhline(_median_spend, color=GEN_COLORS['accent'], linestyle='--',
                   linewidth=1, alpha=0.5)
        ax.axvline(0, color=GEN_COLORS['muted'], linestyle='-', linewidth=0.5, alpha=0.5)

        ax.text(0.98, 0.98,
                f"Top-right = highest risk\n(high spend, steep decline)",
                transform=ax.transAxes, ha='right', va='top',
                fontsize=14, color=GEN_COLORS['accent'],
                fontweight='bold', style='italic')

        ax.set_title("Early Warning: At-Risk Account Map",
                     fontsize=26, fontweight='bold',
                     color=GEN_COLORS['dark_text'], pad=35, loc='left')
        ax.text(0.0, 1.02,
                f"Bubble size = prior spend level  |  Color = warning signal count  ({DATASET_LABEL})",
                transform=ax.transAxes, fontsize=16,
                color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.show()

        # Summary stats
        _high_risk = _at_risk[_at_risk['warning_signals'] >= 2]
        print(f"    Total at-risk accounts: {len(_at_risk):,}")
        print(f"    High-risk (2+ signals): {len(_high_risk):,}")
        if len(_high_risk) > 0:
            _high_risk_spend = _high_risk['prior_3mo_avg_spend'].sum() * 12
            print(f"    High-risk annualized spend at stake: ${_high_risk_spend:,.0f}")
