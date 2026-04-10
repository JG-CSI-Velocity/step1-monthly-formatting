# ===========================================================================
# VELOCITY SCATTER: Spend vs Swipe Velocity by Risk Tier (Conference Edition)
# ===========================================================================
# Each dot = 1 account. Quadrant lines at 1.0 on both axes.

# ---------------------------------------------------------------------------
# Prepare data (sample down for readability)
# ---------------------------------------------------------------------------
MAX_POINTS = 5000
_scatter_df = attrition_df[['spend_velocity', 'swipe_velocity', 'risk_tier']].copy()

# Cap extreme outliers for visual clarity
VEL_CAP = 4.0
_scatter_df['spend_velocity'] = _scatter_df['spend_velocity'].clip(0, VEL_CAP)
_scatter_df['swipe_velocity'] = _scatter_df['swipe_velocity'].clip(0, VEL_CAP)

if len(_scatter_df) > MAX_POINTS:
    _scatter_df = _scatter_df.sample(n=MAX_POINTS, random_state=42)

# ---------------------------------------------------------------------------
# Scatter plot
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 10))

for tier in RISK_ORDER:
    tier_data = _scatter_df[_scatter_df['risk_tier'] == tier]
    if len(tier_data) == 0:
        continue
    ax.scatter(
        tier_data['spend_velocity'],
        tier_data['swipe_velocity'],
        c=RISK_PALETTE[tier],
        label=f"{tier} ({len(tier_data):,})",
        alpha=0.45,
        s=25,
        edgecolors='white',
        linewidth=0.3,
    )

# Quadrant lines at 1.0
ax.axvline(x=1.0, color=GEN_COLORS['muted'], linewidth=2, linestyle='--', alpha=0.7)
ax.axhline(y=1.0, color=GEN_COLORS['muted'], linewidth=2, linestyle='--', alpha=0.7)

# Quadrant labels
_label_props = dict(fontsize=12, fontweight='bold', alpha=0.6, ha='center', va='center')
ax.text(0.5, 0.5, "Declining\nBoth", color=GEN_COLORS['accent'], **_label_props)
ax.text(2.5, 0.5, "Spend Up\nSwipes Down", color=GEN_COLORS['warning'], **_label_props)
ax.text(0.5, 2.5, "Swipes Up\nSpend Down", color=GEN_COLORS['warning'], **_label_props)
ax.text(2.5, 2.5, "Growing\nBoth", color=GEN_COLORS['success'], **_label_props)

# Format
gen_clean_axes(ax, keep_left=True, keep_bottom=True)
ax.set_xlabel("Spend Velocity (annualized 3mo / 12mo ratio)",
              fontsize=16, fontweight='bold', labelpad=10)
ax.set_ylabel("Swipe Velocity (annualized 3mo / 12mo ratio)",
              fontsize=16, fontweight='bold', labelpad=10)

ax.legend(title="Risk Tier", fontsize=12, title_fontsize=13,
          loc='upper right', frameon=True, framealpha=0.9,
          edgecolor=GEN_COLORS['grid'])

ax.set_title("Spend vs Swipe Velocity",
             fontsize=24, fontweight='bold',
             color=GEN_COLORS['dark_text'], pad=35, loc='left')
ax.text(0.0, 1.02,
        f"Each dot = 1 account (sampled to {len(_scatter_df):,}) | 1.0 = steady state",
        transform=ax.transAxes, fontsize=14,
        color=GEN_COLORS['muted'], style='italic')

plt.tight_layout()
plt.show()

# Callout
_q1 = len(_scatter_df[(_scatter_df['spend_velocity'] < 1.0) & (_scatter_df['swipe_velocity'] < 1.0)])
_q4 = len(_scatter_df[(_scatter_df['spend_velocity'] > 1.0) & (_scatter_df['swipe_velocity'] > 1.0)])
print(f"\n    INSIGHT: {_q1:,} accounts ({_q1/len(_scatter_df)*100:.1f}%) below 1.0 on both axes")
print(f"    INSIGHT: {_q4:,} accounts ({_q4/len(_scatter_df)*100:.1f}%) above 1.0 on both axes")
