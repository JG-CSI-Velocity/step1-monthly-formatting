# ===========================================================================
# DORMANCY FUNNEL: Account Health Distribution (Conference Edition)
# ===========================================================================
# Horizontal stacked bar showing Active -> Declining -> Cooling -> Dormant -> Closed.
# Color gradient: green -> yellow -> orange -> grey -> red. (14,7).

if 'retention_df' not in dir() or len(retention_df) == 0:
    print("    No retention data available. Skipping dormancy funnel.")
else:
    _status_counts = []
    _total = len(retention_df)

    for _status in HEALTH_ORDER:
        _count = (retention_df['health_status'] == _status).sum()
        _avg_spend = retention_df.loc[retention_df['health_status'] == _status, 'last_3mo_avg_spend'].mean()
        _status_counts.append({
            'status': _status,
            'count': _count,
            'pct': _count / _total * 100 if _total > 0 else 0,
            'avg_spend': _avg_spend if not np.isnan(_avg_spend) else 0,
        })

    _funnel_df = pd.DataFrame(_status_counts)

    fig, ax = plt.subplots(figsize=(14, 7))

    y = range(len(_funnel_df))
    colors = [HEALTH_PALETTE.get(s, GEN_COLORS['muted']) for s in _funnel_df['status']]

    bars = ax.barh(y, _funnel_df['count'], color=colors,
                   edgecolor='white', linewidth=1, height=0.6)

    # Labels
    for bar, (_, row) in zip(bars, _funnel_df.iterrows()):
        # Count + percentage inside bar (if bar is wide enough)
        _label = f"{int(row['count']):,}  ({row['pct']:.1f}%)"
        _x_pos = bar.get_width() / 2 if bar.get_width() > _funnel_df['count'].max() * 0.15 else bar.get_width() + _funnel_df['count'].max() * 0.02
        _color = 'white' if bar.get_width() > _funnel_df['count'].max() * 0.15 else GEN_COLORS['dark_text']
        ax.text(_x_pos, bar.get_y() + bar.get_height() / 2,
                _label, ha='center' if _color == 'white' else 'left',
                va='center', fontsize=13, fontweight='bold', color=_color)

        # Avg spend outside bar
        if row['avg_spend'] > 0:
            ax.text(bar.get_width() + _funnel_df['count'].max() * 0.01,
                    bar.get_y() + bar.get_height() / 2 - 0.15,
                    f"avg ${row['avg_spend']:,.0f}/mo",
                    ha='left', va='top', fontsize=14,
                    color=GEN_COLORS['muted'], style='italic')

    ax.set_yticks(y)
    ax.set_yticklabels(_funnel_df['status'], fontsize=15, fontweight='bold')
    ax.set_xlabel("Account Count", fontsize=16, fontweight='bold', labelpad=10)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))
    ax.invert_yaxis()

    gen_clean_axes(ax, keep_left=True, keep_bottom=True)
    ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    ax.set_title("Account Health Funnel",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02,
            f"How many accounts are on the path to dormancy?  ({DATASET_LABEL})",
            transform=ax.transAxes, fontsize=16,
            color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.show()
