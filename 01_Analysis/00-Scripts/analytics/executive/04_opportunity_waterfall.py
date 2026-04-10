# ===========================================================================
# OPPORTUNITY WATERFALL: Revenue Opportunity from All Sources
# ===========================================================================
# Shows incremental revenue opportunity from interchange optimization,
# deposit retention, cross-sell, PFI growth, and Reg E optimization.
# Green bars for each segment, connector lines, final total bar.

# ---------------------------------------------------------------------------
# Compute opportunity values from upstream dataframes
# ---------------------------------------------------------------------------
_opp_segments = []

# 1. Interchange optimization (PIN-to-SIG migration)
_ic_opp = 0
if 'interchange_df' in dir() and len(interchange_df) > 0:
    _raw_opp = interchange_df['opportunity'].sum() if 'opportunity' in interchange_df.columns else 0
    _num_months_ic = len(MONTH_LABELS) if 'MONTH_LABELS' in dir() else 12
    _ann_factor = 12.0 / _num_months_ic if _num_months_ic > 0 else 1.0
    _ic_opp = _raw_opp * _ann_factor * 0.40  # 40% capturable
_opp_segments.append(('Interchange\nOptimization', _ic_opp))

# 2. Deposit retention (preventing at-risk account flight)
_retention_opp = 0
if 'attrition_df' in dir() and len(attrition_df) > 0:
    if 'last_12mo_spend' in attrition_df.columns:
        _spend_at_risk = attrition_df[
            attrition_df['risk_tier'].isin(['Declining', 'Dormant'])
        ]['last_12mo_spend'].sum()
        _retention_opp = _spend_at_risk * 0.30  # 30% retention lift
_opp_segments.append(('Deposit\nRetention', _retention_opp))

# 3. Cross-sell revenue (single-product -> multi-product)
_crosssell_opp = 0
if 'rel_df' in dir() and len(rel_df) > 0 and 'product_count' in rel_df.columns:
    _single_ct = (rel_df['product_count'] == 1).sum()
    _crosssell_opp = _single_ct * 0.15 * 2000  # 15% conversion, $2K balance lift
_opp_segments.append(('Cross-Sell\nRevenue', _crosssell_opp))

# 4. PFI growth (secondary -> primary tier migration)
_pfi_opp = 0
if 'payroll_df' in dir() and len(payroll_df) > 0 and 'pfi_tier' in payroll_df.columns:
    _secondary_ct = len(payroll_df[payroll_df['pfi_tier'] == 'Secondary'])
    _tertiary_ct = len(payroll_df[payroll_df['pfi_tier'] == 'Tertiary'])
    _migration_pool = _secondary_ct + _tertiary_ct
    _pfi_opp = _migration_pool * 0.10 * 5000 * 0.03  # 10% migrate, $5K bal, 3% NIM
_opp_segments.append(('PFI\nGrowth', _pfi_opp))

# 5. Reg E optimization (maintaining/increasing opt-in rates)
_rege_opp = 0
if 'rege_df' in dir() and len(rege_df) > 0:
    _opted_out = len(rege_df[rege_df['current_status'] == 'Opted-Out'])
    _rege_opp = _opted_out * 0.10 * 50  # 10% conversion, $50/year fee revenue
_opp_segments.append(('Reg E\nOptimization', _rege_opp))

# Grand total
_grand_total = sum(v for _, v in _opp_segments)

# ---------------------------------------------------------------------------
# Build waterfall chart
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(16, 8))

_labels = [seg[0] for seg in _opp_segments] + ['TOTAL']
_values = [seg[1] for seg in _opp_segments]
_n_bars = len(_opp_segments)

# Compute cumulative bottoms for waterfall
_cumulative = [0]
for v in _values:
    _cumulative.append(_cumulative[-1] + v)

# Bar positions
_x = np.arange(len(_labels))
_bar_width = 0.55

# Draw segment bars (green, rising from cumulative base)
for i in range(_n_bars):
    _bottom = _cumulative[i]
    _height = _values[i]
    ax.bar(
        _x[i], _height, _bar_width,
        bottom=_bottom,
        color=GEN_COLORS['success'],
        edgecolor='white',
        linewidth=1.5,
        zorder=3,
    )
    # Value label on bar
    _label_y = _bottom + _height / 2
    ax.text(
        _x[i], _bottom + _height + (_grand_total * 0.015),
        gen_fmt_dollar(_height, None),
        ha='center', va='bottom',
        fontsize=13, fontweight='bold', color=GEN_COLORS['dark_text'],
        zorder=4,
    )

# Draw total bar (primary color, from 0)
ax.bar(
    _x[-1], _grand_total, _bar_width,
    bottom=0,
    color=GEN_COLORS['primary'],
    edgecolor='white',
    linewidth=1.5,
    zorder=3,
)
ax.text(
    _x[-1], _grand_total + (_grand_total * 0.015),
    gen_fmt_dollar(_grand_total, None),
    ha='center', va='bottom',
    fontsize=15, fontweight='bold', color=GEN_COLORS['primary'],
    zorder=4,
)

# Draw connector lines between segments
for i in range(_n_bars - 1):
    _top = _cumulative[i + 1]
    ax.plot(
        [_x[i] + _bar_width / 2, _x[i + 1] - _bar_width / 2],
        [_top, _top],
        color=GEN_COLORS['muted'],
        linewidth=1.2,
        linestyle='--',
        zorder=2,
    )

# Last segment connector to total
_top_last = _cumulative[_n_bars]
ax.plot(
    [_x[_n_bars - 1] + _bar_width / 2, _x[_n_bars] - _bar_width / 2],
    [_top_last, _top_last],
    color=GEN_COLORS['muted'],
    linewidth=1.2,
    linestyle='--',
    zorder=2,
)

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
ax.set_xticks(_x)
ax.set_xticklabels(_labels, fontsize=12, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))

ax.set_title(
    'Revenue Opportunity Waterfall',
    fontsize=26, fontweight='bold', color=GEN_COLORS['dark_text'],
    loc='left', pad=20,
)

_subtitle = f"Estimated annual impact across all analysis areas"
if 'DATASET_LABEL' in dir():
    _subtitle += f" | {DATASET_LABEL}"
ax.text(
    0.0, 1.02, _subtitle,
    fontsize=12, fontstyle='italic', color=GEN_COLORS['muted'],
    ha='left', va='bottom', transform=ax.transAxes,
)

gen_clean_axes(ax)

# Light horizontal gridlines
ax.yaxis.grid(True, alpha=0.3, color=GEN_COLORS['grid'], zorder=1)
ax.set_axisbelow(True)

# Y-axis starts at 0
ax.set_ylim(0, _grand_total * 1.15)

plt.tight_layout()
plt.show()

# ---------------------------------------------------------------------------
# Insight callouts
# ---------------------------------------------------------------------------
# Find the largest opportunity
_sorted_opps = sorted(_opp_segments, key=lambda x: x[1], reverse=True)
_top_opp_name = _sorted_opps[0][0].replace('\n', ' ')
_top_opp_val = _sorted_opps[0][1]

print(f"\n    INSIGHT: Total estimated annual opportunity: {gen_fmt_dollar(_grand_total, None)}")
print(f"    INSIGHT: Largest single opportunity is {_top_opp_name} "
      f"at {gen_fmt_dollar(_top_opp_val, None)} "
      f"({_top_opp_val/_grand_total*100:.0f}% of total)" if _grand_total > 0 else "")

# Breakdown
print(f"\n    Opportunity breakdown:")
for name, val in _opp_segments:
    _pct = (val / _grand_total * 100) if _grand_total > 0 else 0
    print(f"      {name.replace(chr(10), ' '):>25s}: {gen_fmt_dollar(val, None):>10s} ({_pct:.0f}%)")
