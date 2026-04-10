# ===========================================================================
# ACTION SUMMARY: Cross-Sell Prioritization & Recommendations (Conference Ed)
# ===========================================================================
# Findings table + strategic action items for relationship deepening.

if 'rel_df' not in dir() or len(rel_df) == 0:
    print("    No relationship data available. Skipping action summary.")
else:
    # ------------------------------------------------------------------
    # 1. Build findings
    # ------------------------------------------------------------------
    findings = []
    total_members = len(rel_df)

    # Finding: Single-product risk
    single_count = int((rel_df['product_count'] == 1).sum())
    single_pct = single_count / total_members * 100
    findings.append({
        'Category': 'Flight Risk',
        'Finding': (
            f"{single_count:,} members ({single_pct:.0f}%) hold only 1 product -- "
            f"3x more likely to leave"
        ),
        'Implication': 'Immediate cross-sell campaign needed for single-product members',
        'Priority': 'High',
    })

    # Finding: Relationship depth
    avg_products = rel_df['product_count'].mean()
    three_plus = int((rel_df['product_count'] >= 3).sum())
    three_plus_pct = three_plus / total_members * 100
    findings.append({
        'Category': 'Relationship Depth',
        'Finding': (
            f"Avg {avg_products:.1f} products/member; {three_plus:,} ({three_plus_pct:.0f}%) "
            f"hold 3+ products"
        ),
        'Implication': (
            'Deepening relationships from 1 to 2 products is the highest-leverage move'
        ),
        'Priority': 'High',
    })

    # Finding: Value multiplier
    base_spend = rel_df.loc[rel_df['product_count'] == 1, 'total_spend'].mean()
    multi_spend = rel_df.loc[rel_df['product_count'] >= 3, 'total_spend'].mean()
    if base_spend > 0 and multi_spend > 0:
        spend_mult = multi_spend / base_spend
        findings.append({
            'Category': 'Value Multiplier',
            'Finding': (
                f"Members with 3+ products spend {spend_mult:.1f}x more than "
                f"single-product members"
            ),
            'Implication': 'Each cross-sell directly increases revenue per member',
            'Priority': 'High',
        })

    # Finding: Top cross-sell gaps (from cross-sell matrix data if available)
    try:
        if 'gap_matrix' in dir():
            stacked = gap_matrix.stack().sort_values(ascending=False)
            top_gaps = stacked.head(3)
            gap_items = []
            for (held, target), count in top_gaps.items():
                if not np.isnan(count):
                    gap_items.append(f"{int(count):,} {held} members lack {target}")
            if gap_items:
                findings.append({
                    'Category': 'Cross-Sell Gaps',
                    'Finding': ' | '.join(gap_items[:3]),
                    'Implication': 'Focus campaigns on largest product gaps by volume',
                    'Priority': 'High',
                })
    except Exception:
        pass

    # Finding: Leakage (if available)
    if HAS_FINSERV:
        try:
            if 'finserv_summary_df' in dir() and len(finserv_summary_df) > 0:
                total_leakage = finserv_summary_df['unique_accounts'].sum()
                top_cat = finserv_summary_df.iloc[0]
                cat_name = top_cat.get('category', top_cat.get('Category', 'Unknown'))
                cat_accts = top_cat.get('unique_accounts', top_cat.get('Accounts', 0))
                findings.append({
                    'Category': 'Competitive Leakage',
                    'Finding': (
                        f"{total_leakage:,} members using external financial services; "
                        f"top category: {cat_name} ({int(cat_accts):,} members)"
                    ),
                    'Implication': 'Recapture opportunity through competitive product matching',
                    'Priority': 'Medium',
                })
        except Exception:
            pass

    # Finding: Branch variation (if available)
    if 'branch' in rel_df.columns and rel_df['branch'].notna().sum() > 0:
        branch_avg = rel_df.groupby('branch')['product_count'].mean()
        min_branch_members = max(20, total_members * 0.005)
        branch_counts = rel_df.groupby('branch')['account_number'].count()
        valid_branches = branch_counts[branch_counts >= min_branch_members].index
        branch_avg = branch_avg[branch_avg.index.isin(valid_branches)]
        if len(branch_avg) > 1:
            shallowest = branch_avg.idxmin()
            deepest = branch_avg.idxmax()
            findings.append({
                'Category': 'Branch Variation',
                'Finding': (
                    f"Deepest: {deepest} ({branch_avg[deepest]:.1f} products/member) vs "
                    f"Shallowest: {shallowest} ({branch_avg[shallowest]:.1f} products/member)"
                ),
                'Implication': 'Share best practices from deep-relationship branches',
                'Priority': 'Medium',
            })

    # Finding: Inactive single-product members
    inactive_single = rel_df[
        (rel_df['product_count'] == 1) & (rel_df['active_last_3mo'] == 0)
    ]
    if len(inactive_single) > 0:
        findings.append({
            'Category': 'Dormant Risk',
            'Finding': (
                f"{len(inactive_single):,} single-product members inactive in last 3 months "
                f"({len(inactive_single)/total_members*100:.1f}% of all members)"
            ),
            'Implication': 'Highest attrition risk -- re-engagement before cross-sell',
            'Priority': 'High',
        })

    # ------------------------------------------------------------------
    # 2. Styled findings table
    # ------------------------------------------------------------------
    findings_df = pd.DataFrame(findings)

    priority_colors = {
        'High': 'background-color: #FDECEA; color: #E63946; font-weight: bold',
        'Medium': 'background-color: #FFF8E1; color: #FF9F1C; font-weight: bold',
        'Low': 'background-color: #E8F5E9; color: #2EC4B6; font-weight: bold',
    }

    styled_findings = (
        findings_df.style
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
        .set_caption("Relationship Depth Analysis: Key Findings")
    )

    display(styled_findings)

    # ------------------------------------------------------------------
    # 3. Strategic action items
    # ------------------------------------------------------------------
    actions = []

    # Action 1: Single-product campaign
    actions.append(
        f"Launch single-product cross-sell campaign targeting {single_count:,} "
        f"single-product members -- focus on the 1-to-2 product jump"
    )

    # Action 2: Next best product (if data exists)
    try:
        if 'rec_df' in dir() and len(rec_df) > 0:
            top_rec = rec_df.iloc[0]
            actions.append(
                f"Priority cross-sell: recommend {top_rec['Next Best Product'][:25]} "
                f"to {int(top_rec['target_count']):,} {top_rec['Current Product'][:25]} members"
            )
    except Exception:
        actions.append(
            "Identify next-best-product for each single-product segment "
            "based on multi-holder co-occurrence patterns"
        )

    # Action 3: Dormant re-engagement
    if len(inactive_single) > 0:
        actions.append(
            f"Re-engage {len(inactive_single):,} dormant single-product members before "
            f"attempting cross-sell -- activation first, expansion second"
        )

    # Action 4: Branch coaching
    if 'branch' in rel_df.columns and rel_df['branch'].notna().sum() > 0:
        actions.append(
            "Develop branch-level cross-sell targets and share best practices "
            "from highest-depth branches"
        )

    # Action 5: Leakage recapture
    if HAS_FINSERV:
        actions.append(
            "Create competitive recapture campaigns for members using external "
            "financial services -- match or beat competitor product terms"
        )

    # Action 6: Loyalty program
    actions.append(
        "Implement relationship pricing: reward members at 3+ products with "
        "better rates, reduced fees, or enhanced benefits"
    )

    # Action 7: Onboarding
    actions.append(
        "Redesign new-member onboarding to include second-product recommendation "
        "within first 90 days of account opening"
    )

    actions_df = pd.DataFrame({
        'Action Item': actions,
        'Status': ['Recommended'] * len(actions),
    })

    styled_actions = (
        actions_df.style
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
        .set_caption("Cross-Sell Strategy: Recommended Actions")
    )

    display(styled_actions)

    # ------------------------------------------------------------------
    # 4. Executive summary print
    # ------------------------------------------------------------------
    print(f"\n{'='*70}")
    print(f"  RELATIONSHIP DEPTH: EXECUTIVE SUMMARY")
    print(f"{'='*70}")
    print(f"  Members analyzed:        {total_members:,}")
    print(f"  Avg products/member:     {avg_products:.1f}")
    print(f"  Single-product (risk):   {single_count:,} ({single_pct:.0f}%)")
    print(f"  3+ products (sticky):    {three_plus:,} ({three_plus_pct:.0f}%)")
    if base_spend > 0 and multi_spend > 0:
        print(f"  Value multiplier (3+):   {spend_mult:.1f}x")
    if len(inactive_single) > 0:
        print(f"  Dormant single-product:  {len(inactive_single):,}")
    print(f"  Dataset period:          {DATASET_LABEL}")
    print(f"{'='*70}")
