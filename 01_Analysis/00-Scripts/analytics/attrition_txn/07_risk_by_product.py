# ===========================================================================
# RISK BY PRODUCT: Which Products Have Highest Attrition? (Conference Edition)
# ===========================================================================
# Bar chart: risk tier distribution by product type.

# ---------------------------------------------------------------------------
# Prepare data
# ---------------------------------------------------------------------------
if 'prod_desc' not in attrition_df.columns and 'prod_code' not in attrition_df.columns:
    print("    No product data available in attrition_df -- skipping chart.")
else:
    _prod_col = 'prod_desc' if 'prod_desc' in attrition_df.columns else 'prod_code'

    # Count accounts per product per risk tier
    _prod_risk = (
        attrition_df.groupby([_prod_col, 'risk_tier'])
        .size()
        .reset_index(name='count')
    )

    # Total per product for sorting
    _prod_totals = (
        attrition_df.groupby(_prod_col)
        .size()
        .reset_index(name='total')
        .sort_values('total', ascending=False)
    )

    # At-risk percentage per product
    _prod_at_risk = (
        attrition_df[attrition_df['risk_tier'].isin(['Declining', 'Dormant'])]
        .groupby(_prod_col).size()
        .reset_index(name='at_risk_count')
    )
    _prod_totals = _prod_totals.merge(_prod_at_risk, on=_prod_col, how='left')
    _prod_totals['at_risk_count'] = _prod_totals['at_risk_count'].fillna(0)
    _prod_totals['at_risk_pct'] = (
        _prod_totals['at_risk_count'] / _prod_totals['total'] * 100
    )

    # Top 15 products by total accounts
    _top_prods = _prod_totals.head(15)[_prod_col].tolist()
    _plot_data = _prod_risk[_prod_risk[_prod_col].isin(_top_prods)]

    # Pivot for stacked bar
    _pivot = _plot_data.pivot_table(
        index=_prod_col, columns='risk_tier', values='count', fill_value=0
    )
    _pivot = _pivot.reindex(columns=[t for t in RISK_ORDER if t in _pivot.columns], fill_value=0)

    # Sort by at-risk percentage (highest at top)
    _sort_order = (
        _prod_totals[_prod_totals[_prod_col].isin(_top_prods)]
        .sort_values('at_risk_pct', ascending=True)[_prod_col]
        .tolist()
    )
    _pivot = _pivot.reindex([p for p in _sort_order if p in _pivot.index])

    # ---------------------------------------------------------------------------
    # Stacked horizontal bar chart
    # ---------------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, max(8, len(_top_prods) * 0.6)))

    _pivot.plot(
        kind='barh', stacked=True, ax=ax,
        color=[RISK_PALETTE[t] for t in _pivot.columns],
        edgecolor='white', linewidth=0.5,
        width=0.7,
    )

    # Add at-risk % annotation
    for i, prod in enumerate(_pivot.index):
        _total = _pivot.loc[prod].sum()
        _ar_row = _prod_totals[_prod_totals[_prod_col] == prod]
        _ar_pct = _ar_row['at_risk_pct'].iloc[0] if len(_ar_row) > 0 else 0
        ax.text(_total + (_pivot.values.sum() * 0.005), i,
                f"{_ar_pct:.0f}% at risk",
                va='center', fontsize=11, fontweight='bold',
                color=GEN_COLORS['accent'] if _ar_pct > 30 else GEN_COLORS['dark_text'])

    ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))
    gen_clean_axes(ax, keep_left=True, keep_bottom=True)
    ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    ax.set_xlabel("Account Count", fontsize=16, fontweight='bold', labelpad=10)

    ax.legend(title="Risk Tier", fontsize=12, title_fontsize=13,
              loc='lower right', frameon=True, framealpha=0.9,
              edgecolor=GEN_COLORS['grid'])

    ax.set_title("Attrition Risk by Product",
                 fontsize=24, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02,
            f"Which card products are losing members? | {DATASET_LABEL}",
            transform=ax.transAxes, fontsize=14,
            color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.show()

    # Callout
    _worst_prod = _prod_totals.sort_values('at_risk_pct', ascending=False).iloc[0]
    print(f"\n    INSIGHT: Highest at-risk product: {_worst_prod[_prod_col]} "
          f"({_worst_prod['at_risk_pct']:.1f}% declining/dormant, "
          f"{int(_worst_prod['at_risk_count']):,} accounts)")
