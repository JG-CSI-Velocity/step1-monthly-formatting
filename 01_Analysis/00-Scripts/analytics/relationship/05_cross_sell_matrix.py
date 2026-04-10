# ===========================================================================
# CROSS-SELL MATRIX: Product Gap Heatmap (Conference Edition)
# ===========================================================================
# Heatmap: rows = Product A (held), columns = Product B (NOT held).
# Cell value = count of members who have A but NOT B.
# Identifies biggest cross-sell gaps.

if 'rel_df' not in dir() or len(rel_df) == 0:
    print("    No relationship data available. Skipping cross-sell matrix.")
else:
    # ------------------------------------------------------------------
    # Build member-product matrix
    # ------------------------------------------------------------------
    # Explode product codes to get one row per member-product pair
    member_products = rel_df[['account_number', 'product_codes']].copy()
    member_products = member_products.explode('product_codes')
    member_products.rename(columns={'product_codes': 'product'}, inplace=True)
    member_products['product'] = member_products['product'].astype(str)

    # Get product descriptions for labeling
    if 'product_descriptions' in rel_df.columns:
        desc_map = {}
        for _, row in rel_df.iterrows():
            codes = row['product_codes'] if isinstance(row['product_codes'], list) else []
            descs = row['product_descriptions'] if isinstance(row['product_descriptions'], list) else []
            for c, d in zip(codes, descs):
                if str(c) not in desc_map:
                    desc_map[str(c)] = str(d)
    else:
        desc_map = {}

    # Identify top products by member count (limit for readability)
    product_member_counts = member_products.groupby('product')['account_number'].nunique()
    MIN_MEMBERS_FOR_MATRIX = max(10, len(rel_df) * 0.01)
    top_products = product_member_counts[
        product_member_counts >= MIN_MEMBERS_FOR_MATRIX
    ].sort_values(ascending=False).head(10).index.tolist()

    if len(top_products) < 2:
        print("    Fewer than 2 products with sufficient member counts. Skipping cross-sell matrix.")
    else:
        # Build cross-sell gap matrix
        # For each pair (A held, B not held): count members
        all_members = set(rel_df['account_number'])
        product_holders = {}
        for prod in top_products:
            holders = set(
                member_products[member_products['product'] == prod]['account_number']
            )
            product_holders[prod] = holders

        gap_matrix = pd.DataFrame(index=top_products, columns=top_products, dtype=float)

        for prod_held in top_products:
            for prod_not_held in top_products:
                if prod_held == prod_not_held:
                    gap_matrix.loc[prod_held, prod_not_held] = np.nan
                else:
                    has_a = product_holders[prod_held]
                    has_b = product_holders[prod_not_held]
                    gap_count = len(has_a - has_b)
                    gap_matrix.loc[prod_held, prod_not_held] = gap_count

        gap_matrix = gap_matrix.astype(float)

        # Create readable labels
        def short_label(code):
            desc = desc_map.get(str(code), '')
            if desc and desc != str(code):
                return f"{code}-{desc[:15]}"
            return str(code)[:18]

        row_labels = [short_label(p) for p in top_products]
        col_labels = [short_label(p) for p in top_products]

        # ------------------------------------------------------------------
        # Heatmap
        # ------------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(max(14, len(top_products) * 1.5),
                                        max(7, len(top_products) * 0.9)))

        cmap = LinearSegmentedColormap.from_list(
            'crosssell', ['#F8F9FA', GEN_COLORS['warning'], GEN_COLORS['accent']]
        )
        mask = gap_matrix.isna()

        sns.heatmap(
            gap_matrix, mask=mask, annot=True, fmt=',.0f',
            cmap=cmap, linewidths=2, linecolor='white',
            cbar_kws={'label': 'Members with A but NOT B', 'shrink': 0.8},
            ax=ax, annot_kws={'fontsize': 11, 'fontweight': 'bold'}
        )

        ax.set_xticklabels(col_labels, rotation=45, ha='right',
                           fontsize=14, fontweight='bold')
        ax.set_yticklabels(row_labels, rotation=0,
                           fontsize=14, fontweight='bold')
        ax.set_xlabel("Product NOT Held (Cross-Sell Target)", fontsize=14,
                       fontweight='bold', labelpad=12)
        ax.set_ylabel("Product Held (Current)", fontsize=14,
                       fontweight='bold', labelpad=12)

        ax.set_title("Cross-Sell Opportunity Matrix",
                     fontsize=26, fontweight='bold',
                     color=GEN_COLORS['dark_text'], pad=35, loc='left')
        ax.text(0.0, 1.04,
                f"Members who have Product A but lack Product B  |  {DATASET_LABEL}",
                transform=ax.transAxes, fontsize=14,
                color=GEN_COLORS['muted'], style='italic')

        # Find and annotate the biggest opportunity
        max_gap_val = gap_matrix.max().max()
        if not np.isnan(max_gap_val):
            max_loc = gap_matrix.stack().idxmax()
            held_label = short_label(max_loc[0])
            target_label = short_label(max_loc[1])
            ax.text(0.98, -0.08,
                    f"Biggest gap: {int(max_gap_val):,} {held_label} members lack {target_label}",
                    transform=ax.transAxes, fontsize=13, fontweight='bold',
                    color=GEN_COLORS['accent'], ha='right',
                    bbox=dict(boxstyle='round,pad=0.4', facecolor='#FDECEA',
                              edgecolor=GEN_COLORS['accent'], alpha=0.9))

        plt.tight_layout()
        plt.show()
