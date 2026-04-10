# ===========================================================================
# PRODUCT ACTION SUMMARY: Findings & Recommendations (Conference Edition)
# ===========================================================================
# Conference-styled findings table + strategic action items.

if 'prod_agg' not in dir() or len(prod_agg) == 0:
    print("    No product data available. Skipping action summary.")
else:
    findings_prod = []

    # 1. Dominance
    top_prod = prod_agg.iloc[0]
    findings_prod.append({
        'Category': 'Dominance',
        'Finding': f"{top_prod['product_label'][:30]} = {top_prod['txn_pct']:.1f}% of txns, {int(top_prod['unique_accounts']):,} accounts",
        'Implication': 'Single product dominates -- optimize rewards for this product first',
        'Priority': 'High' if top_prod['txn_pct'] > 50 else 'Medium'
    })

    # 2. Product diversity
    n_prods = len(prod_agg)
    top3_share = prod_agg.head(3)['txn_pct'].sum()
    findings_prod.append({
        'Category': 'Diversity',
        'Finding': f"{n_prods} products total; top 3 = {top3_share:.1f}% of transactions",
        'Implication': 'Product portfolio is ' + ('concentrated' if top3_share > 80 else 'diversified'),
        'Priority': 'Medium'
    })

    # 3. Ticket variation
    min_ticket = prod_agg['avg_spend'].min()
    max_ticket = prod_agg['avg_spend'].max()
    findings_prod.append({
        'Category': 'Ticket Range',
        'Finding': f"Avg ticket ranges ${min_ticket:.2f} to ${max_ticket:.2f} across products",
        'Implication': 'Different products serve different spending profiles',
        'Priority': 'Medium'
    })

    # 4. Activity variation
    min_tpa = prod_agg['txn_per_account'].min()
    max_tpa = prod_agg['txn_per_account'].max()
    findings_prod.append({
        'Category': 'Usage Intensity',
        'Finding': f"Txns/account range: {min_tpa:.1f} to {max_tpa:.1f} across products",
        'Implication': 'Low-activity products may need activation campaigns',
        'Priority': 'High' if max_tpa / max(min_tpa, 0.1) > 5 else 'Medium'
    })

    # ---------------------------------------------------------------------------
    # Styled findings table
    # ---------------------------------------------------------------------------
    findings_df_prod = pd.DataFrame(findings_prod)

    priority_colors = {
        'High': 'background-color: #FDECEA; color: #E63946; font-weight: bold',
        'Medium': 'background-color: #FFF8E1; color: #FF9F1C; font-weight: bold',
        'Low': 'background-color: #E8F5E9; color: #2EC4B6; font-weight: bold',
    }

    styled_findings_prod = (
        findings_df_prod.style
        .hide(axis='index')
        .applymap(lambda v: priority_colors.get(v, ''), subset=['Priority'])
        .set_properties(**{
            'font-size': '13px', 'text-align': 'left',
            'border': '1px solid #E9ECEF', 'padding': '8px 12px',
        })
        .set_properties(subset=['Category'], **{
            'font-weight': 'bold', 'color': GEN_COLORS['primary'],
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
        .set_caption("Card Product Analysis: Key Findings")
    )

    display(styled_findings_prod)

    # ---------------------------------------------------------------------------
    # Action items
    # ---------------------------------------------------------------------------
    actions_prod = [
        f"Optimize rewards program for dominant product: {top_prod['product_label'][:25]}",
        "Create product-specific merchant reward tiers based on usage patterns",
        "Identify low-activity products for targeted activation campaigns",
        "Analyze product migration paths for cross-sell opportunities",
        "Develop product-specific onboarding flows to accelerate early usage",
        "Build product health scorecard tracking volume, spend, and account growth",
    ]

    actions_df_prod = pd.DataFrame({
        'Action Item': actions_prod,
        'Status': ['Recommended'] * len(actions_prod),
    })

    styled_actions_prod = (
        actions_df_prod.style
        .hide(axis='index')
        .set_properties(**{
            'font-size': '13px', 'text-align': 'left',
            'border': '1px solid #E9ECEF', 'padding': '8px 12px',
        })
        .set_properties(subset=['Status'], **{
            'font-weight': 'bold', 'color': GEN_COLORS['primary'],
            'text-align': 'center',
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
        .set_caption("Card Product Strategic Action Items")
    )

    display(styled_actions_prod)
