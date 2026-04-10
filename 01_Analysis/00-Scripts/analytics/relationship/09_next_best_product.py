# ===========================================================================
# NEXT BEST PRODUCT: Cross-Sell Recommendations (Conference Edition)
# ===========================================================================
# For each single-product segment: what do similar multi-product members
# also hold? Builds "Next Best Product" recommendation per current product.

if 'rel_df' not in dir() or len(rel_df) == 0:
    print("    No relationship data available. Skipping next best product.")
else:
    # ------------------------------------------------------------------
    # Build member-product pairs
    # ------------------------------------------------------------------
    member_products = rel_df[['account_number', 'product_codes', 'product_count']].copy()
    member_products = member_products.explode('product_codes')
    member_products.rename(columns={'product_codes': 'product'}, inplace=True)
    member_products['product'] = member_products['product'].astype(str)

    # Get product descriptions for labeling
    desc_map = {}
    if 'product_descriptions' in rel_df.columns:
        for _, row in rel_df.iterrows():
            codes = row['product_codes'] if isinstance(row['product_codes'], list) else []
            descs = row['product_descriptions'] if isinstance(row['product_descriptions'], list) else []
            for c, d in zip(codes, descs):
                if str(c) not in desc_map:
                    desc_map[str(c)] = str(d)

    def product_label(code):
        desc = desc_map.get(str(code), '')
        if desc and desc != str(code):
            return f"{code} - {desc[:25]}"
        return str(code)

    # Products with meaningful member counts
    product_counts = member_products.groupby('product')['account_number'].nunique()
    MIN_MEMBERS = max(10, len(rel_df) * 0.005)
    significant_products = product_counts[product_counts >= MIN_MEMBERS].index.tolist()

    if len(significant_products) < 2:
        print("    Fewer than 2 significant products. Skipping next best product.")
    else:
        # ------------------------------------------------------------------
        # For each product: among multi-product members who hold it,
        # what other products do they also hold?
        # ------------------------------------------------------------------
        recommendations = []

        for source_product in significant_products:
            # Members who hold this product AND have 2+ products
            multi_holders = member_products[
                (member_products['product'] == source_product) &
                (member_products['product_count'] >= 2)
            ]['account_number'].unique()

            if len(multi_holders) == 0:
                continue

            # What other products do these multi-holders have?
            companion_products = member_products[
                (member_products['account_number'].isin(multi_holders)) &
                (member_products['product'] != source_product)
            ]

            companion_counts = (
                companion_products.groupby('product')['account_number']
                .nunique()
                .sort_values(ascending=False)
            )

            if len(companion_counts) == 0:
                continue

            # Top companion = next best product
            next_best = companion_counts.index[0]
            next_best_count = companion_counts.iloc[0]
            next_best_pct = next_best_count / len(multi_holders) * 100

            # Single-product members who hold this product (target audience)
            single_holders = rel_df[
                (rel_df['product_count'] == 1) &
                (rel_df['product_codes'].apply(
                    lambda x: source_product in [str(p) for p in x]
                    if isinstance(x, list) else False
                ))
            ]
            target_count = len(single_holders)

            # Retention uplift proxy: avg products of multi-holders vs single
            avg_products_multi = rel_df[
                rel_df['account_number'].isin(multi_holders)
            ]['product_count'].mean()

            recommendations.append({
                'Current Product': product_label(source_product),
                'Next Best Product': product_label(next_best),
                'Co-Occurrence': f"{next_best_pct:.0f}%",
                'Multi-Holders': int(len(multi_holders)),
                'Single-Product Target': int(target_count),
                'Avg Products (Multi)': round(avg_products_multi, 1),
                'source_code': source_product,
                'next_code': next_best,
                'co_occur_pct': next_best_pct,
                'target_count': target_count,
            })

        if len(recommendations) == 0:
            print("    Could not compute next best product recommendations.")
        else:
            rec_df = pd.DataFrame(recommendations).sort_values(
                'target_count', ascending=False
            ).reset_index(drop=True)

            # ------------------------------------------------------------------
            # Conference-styled recommendation table
            # ------------------------------------------------------------------
            display_cols = [
                'Current Product', 'Next Best Product', 'Co-Occurrence',
                'Single-Product Target', 'Multi-Holders', 'Avg Products (Multi)'
            ]
            rec_display = rec_df[display_cols].copy()

            styled_rec = (
                rec_display.style
                .hide(axis='index')
                .set_properties(**{
                    'font-size': '13px', 'text-align': 'left',
                    'border': '1px solid #E9ECEF', 'padding': '8px 12px',
                })
                .set_properties(subset=['Current Product'], **{
                    'font-weight': 'bold', 'color': GEN_COLORS['primary'],
                })
                .set_properties(subset=['Next Best Product'], **{
                    'font-weight': 'bold', 'color': GEN_COLORS['success'],
                })
                .set_properties(subset=['Co-Occurrence', 'Single-Product Target',
                                        'Multi-Holders', 'Avg Products (Multi)'], **{
                    'text-align': 'center',
                })
                .format({
                    'Single-Product Target': '{:,}',
                    'Multi-Holders': '{:,}',
                })
                .set_table_styles([
                    {'selector': 'th', 'props': [
                        ('background-color', GEN_COLORS['primary']),
                        ('color', 'white'), ('font-size', '14px'),
                        ('font-weight', 'bold'), ('text-align', 'center'),
                        ('padding', '8px 12px'),
                    ]},
                    {'selector': 'caption', 'props': [
                        ('font-size', '22px'), ('font-weight', 'bold'),
                        ('color', GEN_COLORS['dark_text']), ('text-align', 'left'),
                        ('padding-bottom', '12px'),
                    ]},
                ])
                .set_caption("Next Best Product Recommendations")
            )

            display(styled_rec)

            # ------------------------------------------------------------------
            # Visual: horizontal bar of cross-sell targets
            # ------------------------------------------------------------------
            plot_rec = rec_df.sort_values('target_count', ascending=True).tail(10)

            if len(plot_rec) > 0 and plot_rec['target_count'].sum() > 0:
                fig, ax = plt.subplots(figsize=(14, max(7, len(plot_rec) * 0.6 + 2)))

                bar_labels = [
                    f"{r['Current Product'][:20]} -> {r['Next Best Product'][:20]}"
                    for _, r in plot_rec.iterrows()
                ]
                bar_values = plot_rec['target_count'].values

                n = len(plot_rec)
                bar_colors = [plt.cm.ScalarMappable(
                    cmap=LinearSegmentedColormap.from_list(
                        'rec', [GEN_COLORS['success'], GEN_COLORS['primary']]
                    ),
                    norm=plt.Normalize(0, max(n - 1, 1))
                ).to_rgba(i) for i in range(n)]

                bars = ax.barh(
                    range(n), bar_values, color=bar_colors,
                    edgecolor='white', linewidth=1.5, height=0.65, zorder=3
                )

                ax.set_yticks(range(n))
                ax.set_yticklabels(bar_labels, fontsize=14, fontweight='bold')

                max_val = bar_values.max()
                for j, (val, (_, row)) in enumerate(zip(bar_values, plot_rec.iterrows())):
                    ax.text(val + max_val * 0.015, j,
                            f"{int(val):,} targets ({row['co_occur_pct']:.0f}% co-occur)",
                            va='center', fontsize=14, fontweight='bold',
                            color=GEN_COLORS['dark_text'])

                ax.set_xlabel("Single-Product Members to Target", fontsize=14,
                               fontweight='bold', labelpad=10)
                ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))
                ax.set_xlim(0, max_val * 1.45)

                gen_clean_axes(ax, keep_left=True, keep_bottom=True)
                ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
                ax.set_axisbelow(True)

                ax.set_title("Next Best Product: Cross-Sell Targets",
                             fontsize=26, fontweight='bold',
                             color=GEN_COLORS['dark_text'], pad=35, loc='left')
                ax.text(0.0, 1.02,
                        f"Single-product members and their recommended next product  |  {DATASET_LABEL}",
                        transform=ax.transAxes, fontsize=14,
                        color=GEN_COLORS['muted'], style='italic')

                plt.tight_layout()
                plt.show()

            # Summary
            total_targets = rec_df['target_count'].sum()
            top_rec = rec_df.iloc[0]
            print(f"\n  Next Best Product Summary:")
            print(f"    Total single-product members targetable: {total_targets:,}")
            print(f"    Top recommendation: {top_rec['Current Product'][:30]}")
            print(f"      -> Add {top_rec['Next Best Product'][:30]} ({top_rec['Co-Occurrence']} co-occurrence)")
            print(f"      -> {int(top_rec['target_count']):,} members to target")
