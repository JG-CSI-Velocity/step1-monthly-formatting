# ===========================================================================
# PRODUCT BY ENGAGEMENT: Product Preference by Tier (Conference Edition)
# ===========================================================================
# Grouped bar: product distribution by engagement tier. (14,7).
# Depends on acct_txn_counts from general/17_engagement_data.

if 'prod_agg' not in dir() or len(prod_agg) == 0:
    print("    No product data available. Skipping engagement chart.")
else:
    try:
        engage_lookup_prod = acct_txn_counts[['account', 'tier']].copy()
        engage_lookup_prod.columns = ['primary_account_num', 'engage_tier']

        engage_prod = prod_df.merge(engage_lookup_prod, on='primary_account_num', how='inner')

        top5_prods_e = prod_agg.head(5)['product_label'].tolist()
        engage_prod_filtered = engage_prod[engage_prod['product_label'].isin(top5_prods_e)]

        prod_engage_ct = pd.crosstab(
            engage_prod_filtered['product_label'],
            engage_prod_filtered['engage_tier'],
            normalize='columns'
        ) * 100

        prod_engage_ct = prod_engage_ct[[t for t in ENGAGE_ORDER if t in prod_engage_ct.columns]]

        # Truncate names
        prod_engage_ct.index = [p[:22] for p in prod_engage_ct.index]

        fig, ax = plt.subplots(figsize=(14, 7))

        n_tiers = len(prod_engage_ct.columns)
        n_prods = len(prod_engage_ct)
        bar_width = 0.15
        x = np.arange(n_tiers)

        prod_colors = [GEN_COLORS['primary'], GEN_COLORS['info'], GEN_COLORS['success'],
                        GEN_COLORS['warning'], GEN_COLORS['accent']]

        for i, product in enumerate(prod_engage_ct.index):
            offset = (i - n_prods / 2 + 0.5) * bar_width
            ax.bar(x + offset, prod_engage_ct.loc[product], width=bar_width,
                   label=product, color=prod_colors[i % len(prod_colors)],
                   edgecolor='white', linewidth=0.5)

        ax.set_xticks(x)
        ax.set_xticklabels(prod_engage_ct.columns, fontsize=13, fontweight='bold')
        ax.set_ylabel("% of Tier's Transactions", fontsize=16, fontweight='bold', labelpad=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_pct))

        gen_clean_axes(ax, keep_left=True, keep_bottom=True)
        ax.yaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)

        ax.set_title("Product Preference by Engagement Tier",
                     fontsize=26, fontweight='bold',
                     color=GEN_COLORS['dark_text'], pad=35, loc='left')
        ax.text(0.0, 1.02, "Do power users prefer different card products than dormant accounts?",
                transform=ax.transAxes, fontsize=15,
                color=GEN_COLORS['muted'], style='italic')

        ax.legend(
            loc='upper center', bbox_to_anchor=(0.5, -0.08),
            ncol=5, fontsize=10, frameon=False, title='Product',
            title_fontproperties={'weight': 'bold', 'size': 12}
        )

        plt.tight_layout()
        plt.subplots_adjust(bottom=0.12)
        plt.show()

    except NameError:
        print("    acct_txn_counts not available. Run general/17_engagement_data first.")
