# ===========================================================================
# EARLY WARNING: Transition-Zone Accounts (Conference Edition)
# ===========================================================================
# Accounts with velocity 0.5-0.8: not yet dormant but trending down.
# These are the most recoverable. Bar chart + summary table.

# ---------------------------------------------------------------------------
# Identify transition-zone accounts
# ---------------------------------------------------------------------------
_transition = attrition_df[
    (
        (attrition_df['spend_velocity'].between(0.2, 0.8)) |
        (attrition_df['swipe_velocity'].between(0.2, 0.8))
    ) &
    (~attrition_df['risk_tier'].isin(['Dormant', 'Closed']))
].copy()

_transition_count = len(_transition)
_total = len(attrition_df)
_transition_pct = (_transition_count / _total * 100) if _total > 0 else 0

print(f"    Early warning accounts (velocity 0.2-0.8): {_transition_count:,} "
      f"({_transition_pct:.1f}% of portfolio)")

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
_summary_stats = {
    'Total Accounts': f"{_transition_count:,}",
    '% of Portfolio': f"{_transition_pct:.1f}%",
}

if 'avg_bal' in _transition.columns and _transition_count > 0:
    _summary_stats['Avg Balance'] = f"${_transition['avg_bal'].mean():,.0f}"
    _summary_stats['Total Balance at Risk'] = gen_fmt_dollar(_transition['avg_bal'].sum(), None)

if 'last_12mo_spend' in _transition.columns and _transition_count > 0:
    _summary_stats['Avg Annual Spend'] = f"${_transition['last_12mo_spend'].mean():,.0f}"

if 'spend_velocity' in _transition.columns and _transition_count > 0:
    _summary_stats['Avg Spend Velocity'] = f"{_transition['spend_velocity'].mean():.2f}x"

# ---------------------------------------------------------------------------
# Top products in transition zone
# ---------------------------------------------------------------------------
_prod_col = None
if 'prod_desc' in _transition.columns:
    _prod_col = 'prod_desc'
elif 'prod_code' in _transition.columns:
    _prod_col = 'prod_code'

if _prod_col and _transition_count > 0:
    _trans_prods = (
        _transition.groupby(_prod_col)
        .agg(
            count=('account_number', 'count'),
            avg_bal=('avg_bal', 'mean') if 'avg_bal' in _transition.columns else ('account_number', 'count'),
            avg_velocity=('spend_velocity', 'mean'),
        )
        .sort_values('count', ascending=False)
        .head(10)
        .reset_index()
    )

    # ---------------------------------------------------------------------------
    # Bar chart: transition-zone accounts by product
    # ---------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, max(7, len(_trans_prods) * 0.7)))

    y_pos = range(len(_trans_prods))
    bars = ax.barh(
        y_pos, _trans_prods['count'],
        color=GEN_COLORS['warning'], alpha=0.85,
        edgecolor='white', linewidth=1.5, height=0.6
    )

    ax.set_yticks(y_pos)
    ax.set_yticklabels(_trans_prods[_prod_col], fontsize=13, fontweight='bold')
    ax.invert_yaxis()

    # Value labels
    _max_count = _trans_prods['count'].max()
    for bar, row in zip(bars, _trans_prods.itertuples()):
        width = bar.get_width()
        _vel_text = f" (vel: {row.avg_velocity:.2f}x)" if hasattr(row, 'avg_velocity') else ""
        ax.text(width + (_max_count * 0.01),
                bar.get_y() + bar.get_height() / 2,
                f"{width:,.0f} accounts{_vel_text}",
                va='center', fontsize=12, fontweight='bold',
                color=GEN_COLORS['dark_text'])

    ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))
    gen_clean_axes(ax, keep_left=True, keep_bottom=True)
    ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    ax.set_xlabel("Account Count", fontsize=16, fontweight='bold', labelpad=10)
    ax.set_title("Early Warning: Transition-Zone Accounts by Product",
                 fontsize=22, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02,
            f"Velocity 0.2-0.8x -- trending down but recoverable | {DATASET_LABEL}",
            transform=ax.transAxes, fontsize=14,
            color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.show()

# ---------------------------------------------------------------------------
# Styled summary table
# ---------------------------------------------------------------------------
_summary_display = pd.DataFrame(
    [{'Metric': k, 'Value': v} for k, v in _summary_stats.items()]
)

styled = (
    _summary_display.style
    .hide(axis='index')
    .set_properties(**{
        'font-size': '15px',
        'font-weight': 'bold',
        'text-align': 'left',
        'border': '1px solid #E9ECEF',
        'padding': '10px 16px',
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', GEN_COLORS['primary']),
            ('color', 'white'),
            ('font-size', '16px'),
            ('font-weight', 'bold'),
            ('text-align', 'left'),
            ('padding', '10px 16px'),
        ]},
        {'selector': 'caption', 'props': [
            ('font-size', '22px'),
            ('font-weight', 'bold'),
            ('color', GEN_COLORS['dark_text']),
            ('text-align', 'left'),
            ('padding-bottom', '12px'),
        ]},
    ])
    .set_caption("Early Warning Summary")
)

display(styled)

print(f"\n    INSIGHT: {_transition_count:,} accounts are in the transition zone "
      f"(velocity 0.2-0.8x)")
print(f"    INSIGHT: These accounts are the best candidates for proactive outreach")
