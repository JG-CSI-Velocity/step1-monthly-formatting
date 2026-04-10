# ===========================================================================
# RISK DISTRIBUTION: Account Count by Risk Tier (Conference Edition)
# ===========================================================================
# Horizontal bar chart, color-coded by risk tier.

# ---------------------------------------------------------------------------
# Prepare data
# ---------------------------------------------------------------------------
_total = len(attrition_df)
risk_counts = []
for tier in RISK_ORDER:
    _count = len(attrition_df[attrition_df['risk_tier'] == tier])
    risk_counts.append({
        'tier': tier,
        'count': _count,
        'pct': (_count / _total * 100) if _total > 0 else 0,
    })
risk_counts_df = pd.DataFrame(risk_counts)

# ---------------------------------------------------------------------------
# Horizontal bar chart
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 7))

y_pos = range(len(risk_counts_df))
colors = [RISK_PALETTE[t] for t in risk_counts_df['tier']]

bars = ax.barh(
    y_pos, risk_counts_df['count'],
    color=colors, edgecolor='white', linewidth=1.5, height=0.65
)

ax.set_yticks(y_pos)
ax.set_yticklabels(risk_counts_df['tier'], fontsize=14, fontweight='bold')
ax.invert_yaxis()

# Value labels with percentage
max_count = risk_counts_df['count'].max()
for bar, row in zip(bars, risk_counts_df.itertuples()):
    width = bar.get_width()
    ax.text(width + (max_count * 0.01),
            bar.get_y() + bar.get_height() / 2,
            f"{width:,.0f} accounts ({row.pct:.1f}%)",
            va='center', fontsize=13, fontweight='bold',
            color=GEN_COLORS['dark_text'])

ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))
gen_clean_axes(ax, keep_left=True, keep_bottom=True)
ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
ax.set_axisbelow(True)

ax.set_xlabel("Account Count", fontsize=16, fontweight='bold', labelpad=10)
ax.set_title("Attrition Risk Tier Distribution",
             fontsize=24, fontweight='bold',
             color=GEN_COLORS['dark_text'], pad=35, loc='left')
ax.text(0.0, 1.02, f"Velocity-based risk classification | {DATASET_LABEL}",
        transform=ax.transAxes, fontsize=14,
        color=GEN_COLORS['muted'], style='italic')

plt.tight_layout()
plt.show()

# Callout
_at_risk_pct = risk_counts_df[risk_counts_df['tier'].isin(['Declining', 'Dormant'])]['pct'].sum()
print(f"\n    INSIGHT: {_at_risk_pct:.1f}% of accounts are declining or dormant")
_growing_pct = risk_counts_df[risk_counts_df['tier'] == 'Growing']['pct'].iloc[0]
print(f"    INSIGHT: {_growing_pct:.1f}% of accounts show accelerating usage")
