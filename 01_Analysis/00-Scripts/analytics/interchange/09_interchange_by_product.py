# ===========================================================================
# INTERCHANGE BY PRODUCT CODE
# ===========================================================================
# SIG ratio by Prod Code / Prod Desc. Some card products may default
# to PIN routing -- this chart identifies them.

active = interchange_df[
    (interchange_df['total_pin_dollars'] + interchange_df['total_sig_dollars']) > 0
].copy()

# -----------------------------------------------------------------------
# Determine product column
# -----------------------------------------------------------------------
prod_col = None
if 'Prod Desc' in active.columns and active['Prod Desc'].notna().sum() > 0:
    prod_col = 'Prod Desc'
elif 'Prod Code' in active.columns and active['Prod Code'].notna().sum() > 0:
    prod_col = 'Prod Code'

if prod_col:
    prod_agg = (
        active.groupby(prod_col)
        .agg(
            pin_dollars=('total_pin_dollars', 'sum'),
            sig_dollars=('total_sig_dollars', 'sum'),
            pin_count=('total_pin_count', 'sum'),
            sig_count=('total_sig_count', 'sum'),
            acct_count=('acct_number', 'count'),
            opportunity=('opportunity', 'sum'),
        )
        .reset_index()
    )

    prod_agg['total_dollars'] = prod_agg['pin_dollars'] + prod_agg['sig_dollars']
    prod_agg['sig_ratio'] = np.where(
        prod_agg['total_dollars'] > 0,
        prod_agg['sig_dollars'] / prod_agg['total_dollars'] * 100,
        0
    )
    prod_agg['pin_ic'] = prod_agg['pin_dollars'] * PIN_RATE
    prod_agg['sig_ic'] = prod_agg['sig_dollars'] * SIG_RATE
    prod_agg['total_ic'] = prod_agg['pin_ic'] + prod_agg['sig_ic']

    # Filter to products with meaningful volume (>= 10 accounts)
    prod_agg = prod_agg[prod_agg['acct_count'] >= 10].sort_values(
        'sig_ratio', ascending=True)

    # -----------------------------------------------------------------------
    # Chart: SIG ratio by product (horizontal bar with diverging color)
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, max(7, len(prod_agg) * 0.5)))

    y_pos = np.arange(len(prod_agg))
    display_names = [str(n)[:35] for n in prod_agg[prod_col].values]

    # Color based on SIG ratio zones
    bar_colors = [
        GEN_COLORS['success'] if v >= 60
        else (GEN_COLORS['warning'] if v >= 40
              else GEN_COLORS['accent'])
        for v in prod_agg['sig_ratio']
    ]

    bars = ax.barh(y_pos, prod_agg['sig_ratio'].values,
                   color=bar_colors, alpha=0.85, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(display_names, fontsize=12)
    ax.set_xlabel('SIG Ratio (%)', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 100)

    # Reference lines
    ax.axvline(60, color=GEN_COLORS['success'], linestyle='--',
               linewidth=1.2, alpha=0.5)
    ax.axvline(40, color=GEN_COLORS['accent'], linestyle='--',
               linewidth=1.2, alpha=0.5)
    ax.text(61, len(prod_agg) - 0.5, 'Goal: 60%+',
            fontsize=10, color=GEN_COLORS['success'], fontstyle='italic')

    # Annotations: ratio, count, opportunity
    for i, (_, row) in enumerate(prod_agg.iterrows()):
        label = (f"{row['sig_ratio']:.1f}%  |  "
                 f"n={row['acct_count']:,}  |  "
                 f"opp=${row['opportunity']:,.0f}")
        ax.text(min(row['sig_ratio'] + 1.5, 75), i,
                label, va='center', fontsize=10, fontweight='bold',
                color=GEN_COLORS['dark_text'])

    gen_clean_axes(ax)

    fig.suptitle("SIG Ratio by Card Product -- Routing Defaults",
                 fontsize=24, fontweight='bold', x=0.02, ha='left',
                 color=GEN_COLORS['dark_text'])
    fig.text(0.02, 0.96,
             f"Low SIG ratio may indicate default PIN routing  |  {DATASET_LABEL}",
             fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
             ha='left')

    plt.tight_layout(rect=[0, 0, 1, 0.94])
    plt.show()

    # Flag products that may default to PIN
    pin_default = prod_agg[prod_agg['sig_ratio'] < 40]
    if len(pin_default) > 0:
        print("\nPRODUCTS THAT MAY DEFAULT TO PIN ROUTING (<40% SIG):")
        for _, row in pin_default.iterrows():
            print(f"  {row[prod_col]:<30s}  "
                  f"SIG: {row['sig_ratio']:.1f}%  "
                  f"Accounts: {row['acct_count']:,}  "
                  f"Opportunity: ${row['opportunity']:,.0f}")
    else:
        print("\nNo products below the 40% SIG threshold.")

else:
    print("Product column not available in interchange_df.")
    print("  Skipping product-level interchange analysis.")
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.text(0.5, 0.5,
            'Product data not available in rewards_df',
            ha='center', va='center', fontsize=16, color=GEN_COLORS['muted'],
            transform=ax.transAxes)
    ax.set_axis_off()
    fig.suptitle("SIG Ratio by Card Product",
                 fontsize=24, fontweight='bold', x=0.02, ha='left',
                 color=GEN_COLORS['dark_text'])
    plt.tight_layout()
    plt.show()
