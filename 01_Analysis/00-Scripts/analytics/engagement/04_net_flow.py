# ===========================================================================
# NET ENGAGEMENT FLOW: Monthly Upgraders vs Downgraders (Conference Edition)
# ===========================================================================
# Bar chart: net account flow per month (positive = net upgraders). (14,7).

if 'monthly_transitions' not in dir() or not isinstance(monthly_transitions, pd.DataFrame) or len(monthly_transitions) == 0:
    print("    No monthly transitions available. Skipping net flow chart.")
else:
    fig, ax = plt.subplots(figsize=(14, 7))

    x = range(len(monthly_transitions))
    _net = monthly_transitions['net_migration'].values

    # Color: green if positive (net upgraders), red if negative (net downgraders)
    colors = [GEN_COLORS['success'] if v >= 0 else GEN_COLORS['accent'] for v in _net]

    bars = ax.bar(x, _net, color=colors, edgecolor='white', linewidth=0.5, width=0.6)

    # Labels on bars
    for bar, (_, row) in zip(bars, monthly_transitions.iterrows()):
        _val = row['net_migration']
        _y = _val + (abs(_val) * 0.05 + 10) * (1 if _val >= 0 else -1)
        ax.text(bar.get_x() + bar.get_width() / 2, _y,
                f"{_val:+,.0f}",
                ha='center', va='bottom' if _val >= 0 else 'top',
                fontsize=10, fontweight='bold',
                color=GEN_COLORS['success'] if _val >= 0 else GEN_COLORS['accent'])

    # Zero line
    ax.axhline(0, color=GEN_COLORS['dark_text'], linewidth=1, alpha=0.3)

    # Month labels
    _labels = [f"{row['from_month']}\n->{row['to_month']}" for _, row in monthly_transitions.iterrows()]
    ax.set_xticks(x)
    ax.set_xticklabels(_labels, fontsize=9, fontweight='bold')
    ax.set_ylabel("Net Account Migration", fontsize=16, fontweight='bold', labelpad=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))

    gen_clean_axes(ax, keep_left=True, keep_bottom=True)
    ax.yaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    # Campaign wave markers (if available)
    if 'mail_cols' in dir() and len(mail_cols) > 0:
        _wave_labels = [c.replace(' Mail', '') for c in mail_cols]
        for i, (_, row) in enumerate(monthly_transitions.iterrows()):
            if row['to_month'] in _wave_labels:
                ax.axvline(i, color=GEN_COLORS['warning'], linestyle='--',
                           linewidth=1.5, alpha=0.5)
                ax.text(i, ax.get_ylim()[1] * 0.95, f"Mail\n{row['to_month']}",
                        ha='center', va='top', fontsize=7, fontweight='bold',
                        color=GEN_COLORS['warning'], alpha=0.8)

    ax.set_title("Monthly Net Engagement Migration",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02,
            f"Positive = more accounts upgrading than downgrading  ({DATASET_LABEL})",
            transform=ax.transAxes, fontsize=13,
            color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.show()

    # Summary
    _months_up = (monthly_transitions['net_migration'] > 0).sum()
    _months_down = (monthly_transitions['net_migration'] < 0).sum()
    print(f"    Months with net upgrades: {_months_up}")
    print(f"    Months with net downgrades: {_months_down}")
    print(f"    Avg monthly net migration: {monthly_transitions['net_migration'].mean():+,.0f}")
