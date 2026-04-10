# ===========================================================================
# PRODUCT MERCHANT HEATMAP: Which Products Use Which Merchants (Conference Edition)
# ===========================================================================
# Heatmap: products x top 10 merchants. (14,8).

if 'prod_agg' not in dir() or len(prod_agg) == 0:
    print("    No product data available. Skipping merchant heatmap.")
else:
    top_prods_heat = prod_agg.head(min(8, len(prod_agg)))['product_label'].tolist()
    top10_merchants_prod = combined_df['merchant_consolidated'].value_counts().head(10).index.tolist()

    prod_heat_df = prod_df[
        (prod_df['product_label'].isin(top_prods_heat)) &
        (prod_df['merchant_consolidated'].isin(top10_merchants_prod))
    ]

    prod_merch_pivot = pd.crosstab(
        prod_heat_df['product_label'],
        prod_heat_df['merchant_consolidated'],
        normalize='index'
    ) * 100

    # Truncate names
    prod_merch_pivot.index = [p[:25] for p in prod_merch_pivot.index]
    prod_merch_pivot.columns = [m[:20] for m in prod_merch_pivot.columns]

    fig, ax = plt.subplots(figsize=(14, 8))

    prod_cmap = LinearSegmentedColormap.from_list('prod_heat',
        ['#FFFFFF', GEN_COLORS['info'], GEN_COLORS['primary']])

    sns.heatmap(prod_merch_pivot, annot=True, fmt='.1f', cmap=prod_cmap,
                linewidths=1, linecolor='white', cbar_kws={'label': '% of Product Txns'},
                ax=ax, annot_kws={'fontsize': 10, 'fontweight': 'bold'})

    ax.set_xlabel("Merchant", fontsize=13, fontweight='bold', labelpad=8)
    ax.set_ylabel("Product", fontsize=13, fontweight='bold', labelpad=8)
    ax.tick_params(axis='x', rotation=45, labelsize=10)
    ax.tick_params(axis='y', rotation=0, labelsize=10)

    ax.set_title("Product-Merchant Spending Patterns",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02, "Do different card products have different merchant preferences?",
            transform=ax.transAxes, fontsize=15,
            color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.show()
