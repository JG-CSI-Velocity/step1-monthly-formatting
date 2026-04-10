# ===========================================================================
# OPT-IN TREND: 17-Month Reg E Opt-In Percentage
# ===========================================================================
# Line chart showing whether opt-in rate is growing or eroding over the
# observation window. Includes trend line annotation.

# ---------------------------------------------------------------------------
# Compute monthly opt-in rate
# ---------------------------------------------------------------------------
_monthly_status_counts = (
    monthly_rege
    .groupby(['month_key', 'rege_status'])['account_number']
    .nunique()
    .reset_index(name='accounts')
)

_monthly_totals = (
    monthly_rege
    .groupby('month_key')['account_number']
    .nunique()
    .reset_index(name='total_accounts')
)

_optin_monthly = _monthly_status_counts[
    _monthly_status_counts['rege_status'] == 'Opted-In'
].merge(_monthly_totals, on='month_key', how='right')
_optin_monthly['accounts'] = _optin_monthly['accounts'].fillna(0)
_optin_monthly['optin_pct'] = (
    _optin_monthly['accounts'] / _optin_monthly['total_accounts'] * 100
)

# Sort chronologically
_optin_monthly['month_sort'] = _optin_monthly['month_key'].apply(_month_sort_key)
_optin_monthly = _optin_monthly.sort_values('month_sort').reset_index(drop=True)

# Month labels for x-axis
_x_labels = [f"{m[:3]} '{m[3:]}" for m in _optin_monthly['month_key']]
_x_pos = np.arange(len(_optin_monthly))

# Compute linear trend
_y_vals = _optin_monthly['optin_pct'].values
if len(_y_vals) >= 2:
    _coeffs = np.polyfit(_x_pos, _y_vals, 1)
    _trend_line = np.polyval(_coeffs, _x_pos)
    _slope_per_month = _coeffs[0]
    _trend_direction = "growing" if _slope_per_month > 0.05 else (
        "eroding" if _slope_per_month < -0.05 else "stable"
    )
else:
    _trend_line = _y_vals
    _slope_per_month = 0
    _trend_direction = "insufficient data"

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 7))

ax.plot(_x_pos, _y_vals,
        color=GEN_COLORS['primary'], linewidth=3, marker='o',
        markersize=8, markerfacecolor=GEN_COLORS['success'],
        markeredgecolor=GEN_COLORS['primary'], markeredgewidth=2,
        zorder=3, label='Opt-In Rate')

ax.plot(_x_pos, _trend_line,
        color=GEN_COLORS['accent'], linewidth=2, linestyle='--',
        alpha=0.7, label='Trend Line')

# Fill under curve
ax.fill_between(_x_pos, _y_vals, alpha=0.08, color=GEN_COLORS['success'])

# Data labels on first, last, and min/max points
_highlight_idx = {0, len(_y_vals) - 1}
if len(_y_vals) > 2:
    _highlight_idx.add(int(np.argmax(_y_vals)))
    _highlight_idx.add(int(np.argmin(_y_vals)))

for i in _highlight_idx:
    ax.annotate(
        f"{_y_vals[i]:.1f}%",
        xy=(_x_pos[i], _y_vals[i]),
        xytext=(0, 14), textcoords='offset points',
        fontsize=13, fontweight='bold', color=GEN_COLORS['dark_text'],
        ha='center', va='bottom',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  edgecolor=GEN_COLORS['grid'], alpha=0.9)
    )

# Trend annotation
_trend_color = GEN_COLORS['success'] if _trend_direction == 'growing' else (
    GEN_COLORS['accent'] if _trend_direction == 'eroding' else GEN_COLORS['muted']
)
_arrow = "^" if _slope_per_month > 0 else ("v" if _slope_per_month < 0 else "-")
ax.text(
    0.98, 0.95,
    f"Trend: {_trend_direction.upper()}\n"
    f"{_arrow} {abs(_slope_per_month):.2f} pp/month",
    transform=ax.transAxes, fontsize=14, fontweight='bold',
    color=_trend_color, ha='right', va='top',
    bbox=dict(boxstyle='round,pad=0.5', facecolor=_trend_color,
              alpha=0.10, edgecolor=_trend_color)
)

ax.set_xticks(_x_pos)
ax.set_xticklabels(_x_labels, rotation=45, ha='right', fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_pct))
gen_clean_axes(ax)
ax.set_ylabel("Opt-In Rate (%)", fontsize=16, fontweight='bold')

ax.set_title("Reg E Opt-In Rate Over Time",
             fontsize=26, fontweight='bold', loc='left',
             color=GEN_COLORS['dark_text'], pad=20)
ax.text(0.0, 1.02, f"Is overdraft enrollment growing or eroding? | {DATASET_LABEL}",
        transform=ax.transAxes, fontsize=14, color=GEN_COLORS['muted'],
        style='italic')

ax.legend(loc='lower left', fontsize=12)
plt.tight_layout()
plt.show()

print(f"\n    INSIGHT: Opt-in rate trend is {_trend_direction} "
      f"({_slope_per_month:+.2f} percentage points per month)")
print(f"    INSIGHT: Start: {_y_vals[0]:.1f}% -> End: {_y_vals[-1]:.1f}%"
      if len(_y_vals) >= 2 else "    Insufficient data for trend")
