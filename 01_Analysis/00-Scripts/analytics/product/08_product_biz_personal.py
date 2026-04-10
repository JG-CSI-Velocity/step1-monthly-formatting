# ===========================================================================
# PRODUCT BIZ/PERSONAL: Account Type Mix by Product (Conference Edition)
# ===========================================================================
# Stacked bar: business vs personal mix by product. (14,7).

if 'prod_agg' not in dir() or len(prod_agg) == 0:
    print("    No product data available. Skipping biz/personal chart.")
else:
    top_prods_bp = prod_agg.head(min(10, len(prod_agg)))['product_label'].tolist()

    prod_bp = prod_df[prod_df['product_label'].isin(top_prods_bp)]
    prod_bp_ct = pd.crosstab(
        prod_bp['product_label'],
        prod_bp['business_flag'],
        normalize='index'
    ) * 100

    # Sort by personal share
    if 'No' in prod_bp_ct.columns:
        prod_bp_ct = prod_bp_ct.sort_values('No', ascending=True)

    fig, ax = plt.subplots(figsize=(14, 7))

    y_pos = range(len(prod_bp_ct))
    names = [p[:25] for p in prod_bp_ct.index]
    bottom = np.zeros(len(prod_bp_ct))

    bp_colors = {'No': GEN_COLORS['success'], 'Yes': GEN_COLORS['primary']}
    bp_labels = {'No': 'Personal', 'Yes': 'Business'}

    for col in ['No', 'Yes']:
        if col in prod_bp_ct.columns:
            ax.barh(y_pos, prod_bp_ct[col], left=bottom,
                    color=bp_colors.get(col, GEN_COLORS['muted']),
                    label=bp_labels.get(col, col),
                    edgecolor='white', linewidth=0.5, height=0.65)
            bottom += prod_bp_ct[col].values

    ax.set_yticks(y_pos)
    ax.set_yticklabels(names, fontsize=10, fontweight='bold')
    ax.set_xlabel("% of Product Transactions", fontsize=13, fontweight='bold', labelpad=8)
    ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_pct))
    ax.set_xlim(0, 105)

    gen_clean_axes(ax, keep_left=True, keep_bottom=True)
    ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    ax.set_title("Business vs Personal by Product",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02, "Which products skew business vs personal?",
            transform=ax.transAxes, fontsize=15,
            color=GEN_COLORS['muted'], style='italic')

    ax.legend(
        loc='upper center', bbox_to_anchor=(0.5, -0.08),
        ncol=2, fontsize=12, frameon=False, title='Account Type',
        title_fontproperties={'weight': 'bold', 'size': 13}
    )

    plt.tight_layout()
    plt.subplots_adjust(bottom=0.12)
    plt.show()
