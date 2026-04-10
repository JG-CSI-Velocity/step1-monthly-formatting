# ===========================================================================
# PRODUCT DISTRIBUTION: Products by Volume (Conference Edition)
# ===========================================================================
# Horizontal bar: all products by txn volume share. (14,7).

if 'prod_agg' not in dir() or len(prod_agg) == 0:
    print("    No product data available. Skipping distribution bar.")
else:
    fig, ax = plt.subplots(figsize=(14, 7))

    plot_data = prod_agg.head(15).sort_values('txn_pct', ascending=True)
    names = [p[:30] for p in plot_data['product_label']]
    y_pos = range(len(plot_data))

    n = len(plot_data)
    bar_colors = [plt.cm.ScalarMappable(
        cmap=LinearSegmentedColormap.from_list('prod', [GEN_COLORS['info'], GEN_COLORS['primary']]),
        norm=plt.Normalize(0, n - 1)
    ).to_rgba(i) for i in range(n)]

    ax.barh(y_pos, plot_data['txn_pct'], color=bar_colors,
            edgecolor='white', linewidth=0.5, height=0.7)

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10, fontweight='bold')
    ax.set_xlabel("% of Transactions", fontsize=13, fontweight='bold', labelpad=8)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_pct))

    gen_clean_axes(ax, keep_left=True, keep_bottom=True)
    ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    max_val = plot_data['txn_pct'].max()
    for j, (_, row) in enumerate(plot_data.iterrows()):
        ax.text(row['txn_pct'] + max_val * 0.01, j,
                f"{row['txn_pct']:.1f}%",
                va='center', fontsize=9, fontweight='bold',
                color=GEN_COLORS['primary'])

    ax.set_title("Card Product Distribution",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02, "Which card products drive the most transaction volume?",
            transform=ax.transAxes, fontsize=15,
            color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.show()
