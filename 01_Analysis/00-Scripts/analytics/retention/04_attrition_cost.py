# ===========================================================================
# ATTRITION COST: Revenue Impact of Churn (Conference Edition)
# ===========================================================================
# Waterfall chart: Retained vs At-Risk vs Lost revenue. (16,7).

if 'retention_df' not in dir() or len(retention_df) == 0:
    print("    No retention data available. Skipping attrition cost chart.")
else:
    _active = retention_df[retention_df['health_status'] == 'Active']
    _declining = retention_df[retention_df['health_status'].isin(['Declining', 'Cooling'])]
    _dormant = retention_df[retention_df['health_status'] == 'Dormant']
    _closed = retention_df[retention_df['health_status'] == 'Closed']

    # Annualized spend by health status
    _active_rev = _active['last_3mo_avg_spend'].sum() * 12
    _declining_rev = _declining['last_3mo_avg_spend'].sum() * 12
    _dormant_rev = _dormant['prior_3mo_avg_spend'].sum() * 12
    _closed_rev = _closed['pre_close_monthly_spend'].sum() * 12

    categories = [
        'Active\nPortfolio',
        'Declining\n& Cooling',
        'Dormant',
        'Closed\nAccounts',
        'Total\nPortfolio',
    ]
    values = [_active_rev, -_declining_rev, -_dormant_rev, -_closed_rev, 0]

    # Waterfall math
    cumulative = np.zeros(len(values))
    bottoms = np.zeros(len(values))
    cumulative[0] = values[0]
    for i in range(1, len(values) - 1):
        bottoms[i] = cumulative[i - 1]
        cumulative[i] = cumulative[i - 1] + values[i]

    # Last bar = total (starts from 0)
    _total_rev = cumulative[-2]
    values[-1] = _total_rev
    bottoms[-1] = 0
    cumulative[-1] = _total_rev

    colors = [
        GEN_COLORS['success'],     # active
        GEN_COLORS['warning'],     # declining
        GEN_COLORS['muted'],       # dormant
        GEN_COLORS['accent'],      # closed
        GEN_COLORS['primary'],     # total
    ]

    fig, ax = plt.subplots(figsize=(16, 7))

    # For declining/dormant/closed, bar goes DOWN from cumulative
    _bar_heights = []
    _bar_bottoms = []
    for i in range(len(values)):
        if i == 0 or i == len(values) - 1:
            _bar_heights.append(values[i])
            _bar_bottoms.append(bottoms[i])
        else:
            _bar_heights.append(abs(values[i]))
            _bar_bottoms.append(cumulative[i])

    bars = ax.bar(categories, _bar_heights, bottom=_bar_bottoms, color=colors,
                  edgecolor='white', linewidth=1.5, width=0.6, alpha=0.90)

    # Value labels
    for i, (bar, val) in enumerate(zip(bars, values)):
        y_pos = _bar_bottoms[i] + _bar_heights[i] / 2
        if i == 0 or i == len(values) - 1:
            label = f"${abs(val):,.0f}"
        else:
            label = f"-${abs(val):,.0f}"
        ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
                label, ha='center', va='center',
                fontsize=13, fontweight='bold', color='white',
                path_effects=[pe.withStroke(linewidth=3, foreground='black')])

    # Connector lines
    for i in range(len(values) - 2):
        ax.plot([i + 0.3, i + 0.7],
                [cumulative[i], cumulative[i]],
                color=GEN_COLORS['muted'], linewidth=1.2, linestyle='--')

    ax.set_ylabel('Annualized Card Spend ($)', fontsize=16, fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))
    gen_clean_axes(ax, keep_left=True, keep_bottom=True)

    fig.suptitle("Portfolio Attrition Cost -- Annualized Spend Impact",
                 fontsize=24, fontweight='bold', x=0.02, ha='left',
                 color=GEN_COLORS['dark_text'])
    fig.text(0.02, 0.92,
             f"What is member disengagement costing the portfolio?  ({DATASET_LABEL})",
             fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'], ha='left')

    plt.tight_layout(rect=[0, 0, 1, 0.90])
    plt.show()

    # Print summary
    _at_risk_total = _declining_rev + _dormant_rev + _closed_rev
    print(f"    Active portfolio spend (annualized): ${_active_rev:,.0f}")
    print(f"    At-risk + lost spend (annualized):   ${_at_risk_total:,.0f}")
    print(f"    Attrition as % of total:             {_at_risk_total / (_active_rev + _at_risk_total) * 100:.1f}%")
