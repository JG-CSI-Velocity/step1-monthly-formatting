# ===========================================================================
# SINGLE-PRODUCT RISK: Profile of Flight-Risk Members (Conference Edition)
# ===========================================================================
# What product do single-product members hold? How active are they?
# Bar chart of single-product members by their one product.

if 'rel_df' not in dir() or len(rel_df) == 0:
    print("    No relationship data available. Skipping single-product risk.")
else:
    single_df = rel_df[rel_df['product_count'] == 1].copy()

    if len(single_df) == 0:
        print("    No single-product members found.")
    else:
        # Extract the single product held
        single_df['single_product'] = single_df['product_codes'].apply(
            lambda x: str(x[0]) if isinstance(x, list) and len(x) > 0 else 'Unknown'
        )

        # Also get description if available
        single_df['single_product_desc'] = single_df['product_descriptions'].apply(
            lambda x: str(x[0]) if isinstance(x, list) and len(x) > 0 else ''
        )

        single_df['product_label'] = single_df.apply(
            lambda r: f"{r['single_product']} - {r['single_product_desc']}"
            if r['single_product_desc'] and r['single_product_desc'] != r['single_product']
            else r['single_product'],
            axis=1
        )

        # -----------------------------------------------------------------------
        # Bar chart: single-product members by product
        # -----------------------------------------------------------------------
        prod_counts = (
            single_df.groupby('product_label')
            .agg(member_count=('account_number', 'count'))
            .reset_index()
            .sort_values('member_count', ascending=True)
        )

        # Limit to top 15 for readability
        if len(prod_counts) > 15:
            prod_counts = prod_counts.tail(15)

        fig, ax = plt.subplots(figsize=(14, max(7, len(prod_counts) * 0.5 + 2)))

        n = len(prod_counts)
        bar_colors = [plt.cm.ScalarMappable(
            cmap=LinearSegmentedColormap.from_list(
                'risk', [GEN_COLORS['warning'], GEN_COLORS['accent']]
            ),
            norm=plt.Normalize(0, max(n - 1, 1))
        ).to_rgba(i) for i in range(n)]

        bars = ax.barh(
            range(n), prod_counts['member_count'],
            color=bar_colors, edgecolor='white', linewidth=1, height=0.65, zorder=3
        )

        ax.set_yticks(range(n))
        ax.set_yticklabels(
            [p[:35] for p in prod_counts['product_label']],
            fontsize=14, fontweight='bold'
        )

        total_single = len(single_df)
        max_val = prod_counts['member_count'].max()

        for j, (_, row) in enumerate(prod_counts.iterrows()):
            pct = row['member_count'] / total_single * 100
            ax.text(
                row['member_count'] + max_val * 0.015, j,
                f"{int(row['member_count']):,} ({pct:.1f}%)",
                va='center', fontsize=14, fontweight='bold',
                color=GEN_COLORS['dark_text']
            )

        ax.set_xlabel("Number of Single-Product Members", fontsize=14,
                       fontweight='bold', labelpad=10)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))
        ax.set_xlim(0, max_val * 1.3)

        gen_clean_axes(ax, keep_left=True, keep_bottom=True)
        ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)

        ax.set_title("Single-Product Members: What Do They Hold?",
                     fontsize=26, fontweight='bold',
                     color=GEN_COLORS['dark_text'], pad=35, loc='left')
        ax.text(0.0, 1.02,
                f"{total_single:,} members with only 1 product -- highest attrition risk  |  {DATASET_LABEL}",
                transform=ax.transAxes, fontsize=14,
                color=GEN_COLORS['accent'], style='italic', fontweight='bold')

        # Callout for largest single-product group
        top_product = prod_counts.iloc[-1]
        top_name = top_product['product_label'][:25]
        ax.text(0.98, 0.05,
                f"{int(top_product['member_count']):,} members have ONLY\n{top_name}",
                transform=ax.transAxes, fontsize=14, fontweight='bold',
                color=GEN_COLORS['accent'], ha='right', va='bottom',
                bbox=dict(boxstyle='round,pad=0.5', facecolor='#FDECEA',
                          edgecolor=GEN_COLORS['accent'], alpha=0.9))

        plt.tight_layout()
        plt.show()

        # -----------------------------------------------------------------------
        # Summary stats for single-product members
        # -----------------------------------------------------------------------
        print(f"\n  Single-product member profile:")
        print(f"    Total: {total_single:,} ({total_single/len(rel_df)*100:.1f}% of all members)")
        print(f"    Avg transactions: {single_df['txn_count'].mean():.1f}")
        print(f"    Avg total spend: ${single_df['total_spend'].mean():,.0f}")
        if 'avg_bal' in single_df.columns:
            print(f"    Avg balance: ${single_df['avg_bal'].mean():,.0f}")
        print(f"    Active in last 3mo: {single_df['active_last_3mo'].mean()*100:.1f}%")
