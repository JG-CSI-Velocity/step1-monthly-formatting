# ===========================================================================
# OD LIMIT TREND: Average Overdraft Limit Over 17 Months
# ===========================================================================
# Line chart tracking average OD limit amount over time. Are limits being
# raised, lowered, or holding steady? Annotate direction.

# ---------------------------------------------------------------------------
# Compute monthly average OD limit
# ---------------------------------------------------------------------------
_monthly_od_avg = (
    od_df
    .dropna(subset=['od_limit'])
    .groupby('month_key')
    .agg(
        avg_od_limit=('od_limit', 'mean'),
        median_od_limit=('od_limit', 'median'),
        total_accounts=('account_number', 'nunique'),
        nonzero_count=('od_limit', lambda x: (x > 0).sum()),
    )
    .reset_index()
)

_monthly_od_avg['month_sort'] = _monthly_od_avg['month_key'].apply(_month_sort_key)
_monthly_od_avg = _monthly_od_avg.sort_values('month_sort').reset_index(drop=True)

# Average only for accounts with non-zero limits
_monthly_od_nonzero = (
    od_df[od_df['od_limit'] > 0]
    .groupby('month_key')['od_limit']
    .mean()
    .reset_index(name='avg_od_nonzero')
)
_monthly_od_avg = _monthly_od_avg.merge(_monthly_od_nonzero, on='month_key', how='left')

_x_labels = [f"{m[:3]} '{m[3:]}" for m in _monthly_od_avg['month_key']]
_x_pos = np.arange(len(_monthly_od_avg))

# Trend computation
_y_all = _monthly_od_avg['avg_od_limit'].values
_y_nonzero = _monthly_od_avg['avg_od_nonzero'].fillna(0).values

if len(_y_all) >= 2:
    _coeffs_all = np.polyfit(_x_pos, _y_all, 1)
    _trend_all = np.polyval(_coeffs_all, _x_pos)
    _slope_all = _coeffs_all[0]
else:
    _trend_all = _y_all
    _slope_all = 0

_direction = "increasing" if _slope_all > 0.5 else (
    "decreasing" if _slope_all < -0.5 else "stable"
)

# ---------------------------------------------------------------------------
# Plot
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 7))

# All accounts average
ax.plot(_x_pos, _y_all,
        color=GEN_COLORS['primary'], linewidth=3, marker='o',
        markersize=8, markerfacecolor=GEN_COLORS['info'],
        markeredgecolor=GEN_COLORS['primary'], markeredgewidth=2,
        zorder=3, label='Avg OD Limit (All Accounts)')

# Non-zero only average
if _y_nonzero.sum() > 0:
    ax.plot(_x_pos, _y_nonzero,
            color=GEN_COLORS['success'], linewidth=2.5, marker='s',
            markersize=6, markerfacecolor=GEN_COLORS['success'],
            markeredgecolor='white', markeredgewidth=1.5,
            zorder=3, label='Avg OD Limit (Non-Zero Only)')

# Trend line
ax.plot(_x_pos, _trend_all,
        color=GEN_COLORS['accent'], linewidth=2, linestyle='--',
        alpha=0.7, label='Trend')

# Fill between the two lines
if _y_nonzero.sum() > 0:
    ax.fill_between(_x_pos, _y_all, _y_nonzero,
                    alpha=0.06, color=GEN_COLORS['info'])

# Annotate start and end values
for idx, y_arr, color in [
    (0, _y_all, GEN_COLORS['primary']),
    (len(_y_all) - 1, _y_all, GEN_COLORS['primary']),
]:
    ax.annotate(
        gen_fmt_dollar(y_arr[idx], None),
        xy=(_x_pos[idx], y_arr[idx]),
        xytext=(0, 16), textcoords='offset points',
        fontsize=13, fontweight='bold', color=color,
        ha='center', va='bottom',
        bbox=dict(boxstyle='round,pad=0.3', facecolor='white',
                  edgecolor=GEN_COLORS['grid'], alpha=0.9)
    )

# Direction annotation box
_dir_color = GEN_COLORS['success'] if _direction == 'increasing' else (
    GEN_COLORS['accent'] if _direction == 'decreasing' else GEN_COLORS['muted']
)
_arrow_symbol = "^" if _slope_all > 0 else ("v" if _slope_all < 0 else "=")
ax.text(
    0.98, 0.95,
    f"Trend: {_direction.upper()}\n"
    f"{_arrow_symbol} ${abs(_slope_all):.2f}/month",
    transform=ax.transAxes, fontsize=14, fontweight='bold',
    color=_dir_color, ha='right', va='top',
    bbox=dict(boxstyle='round,pad=0.5', facecolor=_dir_color,
              alpha=0.10, edgecolor=_dir_color)
)

ax.set_xticks(_x_pos)
ax.set_xticklabels(_x_labels, rotation=45, ha='right', fontsize=12)
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))
gen_clean_axes(ax)
ax.set_ylabel("Average OD Limit", fontsize=16, fontweight='bold')
ax.legend(loc='lower left', fontsize=12)

ax.set_title("Average Overdraft Limit Over Time",
             fontsize=26, fontweight='bold', loc='left',
             color=GEN_COLORS['dark_text'], pad=20)
ax.text(0.0, 1.02,
        f"Are OD limits being raised or lowered? | {DATASET_LABEL}",
        transform=ax.transAxes, fontsize=14, color=GEN_COLORS['muted'],
        style='italic')

plt.tight_layout()
plt.show()

print(f"\n    INSIGHT: OD limit trend is {_direction} "
      f"(${_slope_all:+.2f} per month)")
print(f"    INSIGHT: Start avg: {gen_fmt_dollar(_y_all[0], None)} -> "
      f"End avg: {gen_fmt_dollar(_y_all[-1], None)}"
      if len(_y_all) >= 2 else "    Insufficient data for trend")
