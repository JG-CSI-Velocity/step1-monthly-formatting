# ===========================================================================
# PRODUCT COUNT BAR: Members by Number of Products Held (Conference Edition)
# ===========================================================================
# Bar chart: count of accounts by products held (1, 2, 3, 4, 5+).
# Color gradient from red (1 = risk) to green (5+ = sticky).

if 'rel_df' not in dir() or len(rel_df) == 0:
    print("    No relationship data available. Skipping product count bar.")
else:
    fig, ax = plt.subplots(figsize=(14, 7))

    # Aggregate by product tier
    tier_counts = rel_df['product_tier'].value_counts()
    plot_tiers = []
    for tier in PRODUCT_TIER_ORDER:
        count = tier_counts.get(tier, 0)
        plot_tiers.append({'tier': tier, 'count': count})
    plot_df = pd.DataFrame(plot_tiers)

    total_members = plot_df['count'].sum()
    plot_df['pct'] = plot_df['count'] / total_members * 100

    # Gradient: red (risk) -> amber -> green (sticky)
    RISK_GRADIENT = ['#E63946', '#FF9F1C', '#2EC4B6', '#457B9D', '#1B2A4A']
    bar_colors = RISK_GRADIENT[:len(plot_df)]

    bars = ax.bar(
        range(len(plot_df)), plot_df['count'],
        color=bar_colors, edgecolor='white', linewidth=2, width=0.65, zorder=3
    )

    # Percentage + count labels on each bar
    for i, (_, row) in enumerate(plot_df.iterrows()):
        label_y = row['count'] + total_members * 0.015
        ax.text(i, label_y,
                f"{int(row['count']):,}\n({row['pct']:.1f}%)",
                ha='center', va='bottom', fontsize=14, fontweight='bold',
                color=GEN_COLORS['dark_text'])

    ax.set_xticks(range(len(plot_df)))
    ax.set_xticklabels(
        [f"{t} Product{'s' if t != '1' else ''}" for t in plot_df['tier']],
        fontsize=14, fontweight='bold'
    )
    ax.set_ylabel("Number of Members", fontsize=14, fontweight='bold', labelpad=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))

    gen_clean_axes(ax)
    ax.yaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)
    ax.set_ylim(0, plot_df['count'].max() * 1.25)

    ax.set_title("How Deep Are Member Relationships?",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02,
            f"Members by number of products held  |  {DATASET_LABEL}",
            transform=ax.transAxes, fontsize=15,
            color=GEN_COLORS['muted'], style='italic')

    # Risk annotation
    single_count = plot_df.loc[plot_df['tier'] == '1', 'count'].values
    if len(single_count) > 0 and single_count[0] > 0:
        ax.annotate(
            f"{int(single_count[0]):,} members\nat flight risk",
            xy=(0, single_count[0]),
            xytext=(1.5, single_count[0] * 0.95),
            fontsize=13, fontweight='bold', color=GEN_COLORS['accent'],
            arrowprops=dict(arrowstyle='->', color=GEN_COLORS['accent'], lw=2),
            ha='center'
        )

    plt.tight_layout()
    plt.show()
