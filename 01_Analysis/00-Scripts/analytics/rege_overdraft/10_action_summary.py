# ===========================================================================
# REG E / OVERDRAFT ACTION SUMMARY: Findings & Recommendations
# ===========================================================================
# Consolidated findings from the Reg E analysis with actionable
# recommendations for credit union leadership.

# ---------------------------------------------------------------------------
# Gather key metrics from upstream cells
# ---------------------------------------------------------------------------
_total = len(rege_df)
_opted_in = len(rege_df[rege_df['current_status'] == 'Opted-In'])
_opted_out = len(rege_df[rege_df['current_status'] == 'Opted-Out'])
_optin_rate = (_opted_in / _total * 100) if _total > 0 else 0
_changed = int(rege_df['status_changed'].sum())
_newly_out = len(rege_df[rege_df['change_direction'] == 'Newly Opted-Out'])
_newly_in = len(rege_df[rege_df['change_direction'] == 'Newly Opted-In'])

# OD limit stats
_avg_od = rege_df.loc[rege_df['current_status'] == 'Opted-In', 'current_od_limit'].mean()
_avg_od = _avg_od if not pd.isna(_avg_od) else 0

# Trend direction (recompute from monthly data)
_optin_monthly = (
    monthly_rege
    .groupby('month_key')
    .apply(lambda g: (g['rege_status'] == 'Opted-In').sum() / len(g) * 100)
    .reset_index(name='optin_pct')
)
_optin_monthly['month_sort'] = _optin_monthly['month_key'].apply(_month_sort_key)
_optin_monthly = _optin_monthly.sort_values('month_sort')
_pct_vals = _optin_monthly['optin_pct'].values

if len(_pct_vals) >= 2:
    _x = np.arange(len(_pct_vals))
    _slope = np.polyfit(_x, _pct_vals, 1)[0]
    _trend_word = "growing" if _slope > 0.05 else ("eroding" if _slope < -0.05 else "stable")
    _start_pct = _pct_vals[0]
    _end_pct = _pct_vals[-1]
else:
    _slope = 0
    _trend_word = "insufficient data"
    _start_pct = _pct_vals[0] if len(_pct_vals) > 0 else 0
    _end_pct = _start_pct

# Revenue exposure
_est_revenue = _opted_in * 4 * 30  # 4 events/yr x $30 avg fee
_revenue_loss_10pct = _est_revenue * 0.10
_revenue_loss_20pct = _est_revenue * 0.20

# Demographic insights
_demo_findings = []
if 'age_band' in rege_df.columns:
    _age_rates = rege_df.groupby('age_band')['current_status'].apply(
        lambda x: (x == 'Opted-In').sum() / len(x) * 100
    ).reset_index(name='optin_pct')
    if len(_age_rates) > 0:
        _lowest_age = _age_rates.loc[_age_rates['optin_pct'].idxmin()]
        _demo_findings.append(
            f"Age band with lowest opt-in: {_lowest_age['age_band']} "
            f"at {_lowest_age['optin_pct']:.1f}%"
        )

if 'balance_band' in rege_df.columns:
    _bal_rates = rege_df.groupby('balance_band')['current_status'].apply(
        lambda x: (x == 'Opted-In').sum() / len(x) * 100
    ).reset_index(name='optin_pct')
    if len(_bal_rates) > 0:
        _lowest_bal = _bal_rates.loc[_bal_rates['optin_pct'].idxmin()]
        _demo_findings.append(
            f"Balance band with lowest opt-in: {_lowest_bal['balance_band']} "
            f"at {_lowest_bal['optin_pct']:.1f}%"
        )

if 'engage_tier' in rege_df.columns:
    _eng_rates = rege_df.groupby('engage_tier')['current_status'].apply(
        lambda x: (x == 'Opted-In').sum() / len(x) * 100
    ).reset_index(name='optin_pct')
    _eng_rates = _eng_rates[_eng_rates['engage_tier'] != 'Unknown']
    if len(_eng_rates) > 0:
        _lowest_eng = _eng_rates.loc[_eng_rates['optin_pct'].idxmin()]
        _demo_findings.append(
            f"Engagement tier with lowest opt-in: {_lowest_eng['engage_tier']} "
            f"at {_lowest_eng['optin_pct']:.1f}%"
        )

# ---------------------------------------------------------------------------
# Build findings text blocks
# ---------------------------------------------------------------------------
_findings = [
    {
        'title': 'Current Opt-In Rate & Trend',
        'color': GEN_COLORS['success'] if _trend_word == 'growing' else (
            GEN_COLORS['accent'] if _trend_word == 'eroding' else GEN_COLORS['info']
        ),
        'lines': [
            f"Current opt-in rate: {_optin_rate:.1f}% ({_opted_in:,} of {_total:,} accounts)",
            f"Trend direction: {_trend_word.upper()} ({_slope:+.2f} pp/month)",
            f"Period: {_start_pct:.1f}% -> {_end_pct:.1f}%",
            f"Status changes observed: {_changed:,} ({_newly_in:,} opted in, {_newly_out:,} opted out)",
        ],
    },
    {
        'title': 'Revenue Exposure',
        'color': GEN_COLORS['warning'],
        'lines': [
            f"Estimated annual OD fee revenue potential: {gen_fmt_dollar(_est_revenue, None)}",
            f"If opt-in drops 10%: -{gen_fmt_dollar(_revenue_loss_10pct, None)}/year",
            f"If opt-in drops 20%: -{gen_fmt_dollar(_revenue_loss_20pct, None)}/year",
            f"Average OD limit (opted-in): {gen_fmt_dollar(_avg_od, None)}",
        ],
    },
    {
        'title': 'Segments With Lowest Opt-In',
        'color': GEN_COLORS['accent'],
        'lines': _demo_findings if _demo_findings else [
            "Demographic breakdowns not available for this dataset"
        ],
    },
    {
        'title': 'Recommendations',
        'color': GEN_COLORS['primary'],
        'lines': [
            "1. Target low-opt-in segments with Reg E education campaigns",
            "2. Monitor monthly opt-in trend; intervene if erosion accelerates",
            "3. Review OD limits for adequacy; consider adjustments by risk profile",
            "4. Assess low-balance opted-out accounts for financial wellness outreach",
            "5. Evaluate fee structure competitiveness vs peer credit unions",
        ],
    },
]

# ---------------------------------------------------------------------------
# Render summary cards
# ---------------------------------------------------------------------------
fig = plt.figure(figsize=(18, 14))
gs = GridSpec(2, 2, hspace=0.35, wspace=0.25)

for idx, finding in enumerate(_findings):
    row = idx // 2
    col = idx % 2
    ax = fig.add_subplot(gs[row, col])
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.axis('off')

    # Card background
    card = FancyBboxPatch(
        (0.02, 0.02), 0.96, 0.96,
        boxstyle="round,pad=0.04",
        facecolor=finding['color'], alpha=0.05,
        edgecolor=finding['color'], linewidth=2.5
    )
    ax.add_patch(card)

    # Title
    ax.text(0.06, 0.90, finding['title'],
            fontsize=18, fontweight='bold', color=finding['color'],
            va='top', transform=ax.transAxes)

    # Divider line
    ax.plot([0.06, 0.94], [0.82, 0.82], color=finding['color'],
            linewidth=1.5, alpha=0.3, transform=ax.transAxes)

    # Bullet points
    _y_start = 0.75
    _line_height = 0.12
    for i, line in enumerate(finding['lines'][:6]):
        _y = _y_start - (i * _line_height)
        if _y < 0.05:
            break
        ax.text(0.08, _y, line,
                fontsize=12, fontweight='normal', color=GEN_COLORS['dark_text'],
                va='top', transform=ax.transAxes, wrap=True,
                fontfamily='sans-serif')

fig.suptitle("Reg E / Overdraft Analysis -- Key Findings",
             fontsize=28, fontweight='bold',
             color=GEN_COLORS['dark_text'], y=1.02)
fig.text(0.5, 0.99,
         f"Action items for credit union leadership | {DATASET_LABEL}",
         fontsize=14, color=GEN_COLORS['muted'], style='italic',
         ha='center')

plt.tight_layout()
plt.show()

# ---------------------------------------------------------------------------
# Print consolidated summary
# ---------------------------------------------------------------------------
print("\n" + "=" * 72)
print("  REG E / OVERDRAFT ANALYSIS COMPLETE")
print("=" * 72)
for finding in _findings:
    print(f"\n  [{finding['title'].upper()}]")
    for line in finding['lines']:
        print(f"    - {line}")
print("\n" + "=" * 72)
