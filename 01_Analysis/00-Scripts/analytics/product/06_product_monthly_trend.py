# ===========================================================================
# PRODUCT MONTHLY TREND: Top Products Over Time (Conference Edition)
# ===========================================================================
# Multi-line: monthly txn share for top 5 products. (14,7).

if 'prod_agg' not in dir() or len(prod_agg) == 0:
    print("    No product data available. Skipping monthly trend.")
else:
    fig, ax = plt.subplots(figsize=(14, 7))

    trend_colors_prod = [GEN_COLORS['primary'], GEN_COLORS['info'], GEN_COLORS['success'],
                          GEN_COLORS['warning'], GEN_COLORS['accent']]
    top5_products = prod_agg.head(5)['product_label'].tolist()

    for i, product in enumerate(top5_products):
        p_data = prod_monthly[prod_monthly['product_label'] == product].sort_values('year_month')
        if len(p_data) == 0:
            continue
        dates = p_data['year_month'].dt.to_timestamp()
        ax.plot(dates, p_data['share_pct'],
                color=trend_colors_prod[i], linewidth=2.5,
                label=product[:25], marker='o', markersize=4, zorder=4)

        # End-of-line label
        last_val = p_data['share_pct'].iloc[-1]
        ax.text(dates.iloc[-1], last_val,
                f"  {product[:18]}", fontsize=9, fontweight='bold',
                color=trend_colors_prod[i], va='center')

    ax.set_ylabel("% of Monthly Transactions", fontsize=16, fontweight='bold', labelpad=10)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_pct))

    gen_clean_axes(ax, keep_left=True, keep_bottom=True)
    ax.yaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    ax.set_xlabel("")
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%b %Y'))
    ax.tick_params(axis='x', rotation=45)

    ax.set_title("Card Product Trends Over Time",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02, "Are product shares stable or is there migration between products?",
            transform=ax.transAxes, fontsize=15,
            color=GEN_COLORS['muted'], style='italic')

    ax.legend(
        loc='upper center', bbox_to_anchor=(0.5, -0.15),
        ncol=3, fontsize=10, frameon=False, title='Product',
        title_fontproperties={'weight': 'bold', 'size': 12}
    )

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.22)
    plt.show()
