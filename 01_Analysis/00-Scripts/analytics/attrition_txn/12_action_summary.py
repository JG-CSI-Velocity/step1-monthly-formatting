# ===========================================================================
# ACTION SUMMARY: Attrition Findings + Recommendations (Conference Edition)
# ===========================================================================
# Styled findings table + printed action items.

# ---------------------------------------------------------------------------
# Build findings from upstream data
# ---------------------------------------------------------------------------
_total = len(attrition_df)
_declining_count = len(attrition_df[attrition_df['risk_tier'] == 'Declining'])
_dormant_count = len(attrition_df[attrition_df['risk_tier'] == 'Dormant'])
_at_risk_count = _declining_count + _dormant_count
_at_risk_pct = (_at_risk_count / _total * 100) if _total > 0 else 0
_growing_count = len(attrition_df[attrition_df['risk_tier'] == 'Growing'])
_growing_pct = (_growing_count / _total * 100) if _total > 0 else 0

findings = []

# Finding 1: At-risk percentage
findings.append({
    'Area': 'Attrition Risk',
    'Finding': f"{_at_risk_pct:.1f}% of the portfolio ({_at_risk_count:,} accounts) "
               f"is declining or dormant",
    'Signal': 'Needs Attention' if _at_risk_pct > 20 else 'Monitor',
})

# Finding 2: Spend at risk
if 'last_12mo_spend' in attrition_df.columns:
    _spend_at_risk = attrition_df[
        attrition_df['risk_tier'].isin(['Declining', 'Dormant'])
    ]['last_12mo_spend'].sum()
    findings.append({
        'Area': 'Revenue Impact',
        'Finding': f"{gen_fmt_dollar(_spend_at_risk, None)} in annual spend at risk "
                   f"from declining/dormant accounts",
        'Signal': 'Needs Attention',
    })

# Finding 3: Growing accounts (positive signal)
findings.append({
    'Area': 'Growth Signal',
    'Finding': f"{_growing_pct:.1f}% of accounts ({_growing_count:,}) show accelerating "
               f"spend and swipe velocity",
    'Signal': 'Positive',
})

# Finding 4: Velocity insight
_avg_declining_vel = attrition_df[
    attrition_df['risk_tier'] == 'Declining'
]['spend_velocity'].mean() if _declining_count > 0 else 0
findings.append({
    'Area': 'Velocity',
    'Finding': f"Declining accounts average {_avg_declining_vel:.2f}x spend velocity "
               f"(less than half their 12-month pace)",
    'Signal': 'Insight',
})

# Finding 5: Competitor insight (if available)
if 'competitor_category' in combined_df.columns:
    _at_risk_accts = set(
        attrition_df[attrition_df['risk_tier'].isin(['Declining', 'Dormant'])]['account_number']
    )
    _comp_txns = combined_df[combined_df['competitor_category'].notna()]
    _accts_with_comp = set(_comp_txns['primary_account_num'].unique())
    _overlap = _at_risk_accts & _accts_with_comp
    _comp_pct = (len(_overlap) / len(_at_risk_accts) * 100) if _at_risk_accts else 0
    findings.append({
        'Area': 'Competition',
        'Finding': f"{_comp_pct:.1f}% of at-risk accounts ({len(_overlap):,}) show "
                   f"competitor transaction activity",
        'Signal': 'Needs Attention' if _comp_pct > 30 else 'Monitor',
    })

# Finding 6: Product concentration
if 'prod_desc' in attrition_df.columns or 'prod_code' in attrition_df.columns:
    _pcol = 'prod_desc' if 'prod_desc' in attrition_df.columns else 'prod_code'
    _at_risk_prods = attrition_df[attrition_df['risk_tier'].isin(['Declining', 'Dormant'])]
    _worst_prod = _at_risk_prods[_pcol].value_counts()
    if len(_worst_prod) > 0:
        findings.append({
            'Area': 'Product Risk',
            'Finding': f"Most at-risk product: {_worst_prod.index[0]} "
                       f"({_worst_prod.iloc[0]:,} declining/dormant accounts)",
            'Signal': 'Insight',
        })

findings_df = pd.DataFrame(findings)

# ---------------------------------------------------------------------------
# Signal color styling
# ---------------------------------------------------------------------------
def _signal_color(val):
    color_map = {
        'Positive': GEN_COLORS['success'],
        'Needs Attention': GEN_COLORS['accent'],
        'Monitor': GEN_COLORS['warning'],
        'Insight': GEN_COLORS['info'],
    }
    c = color_map.get(val, GEN_COLORS['dark_text'])
    return f"color: {c}; font-weight: bold"

styled = (
    findings_df.style
    .hide(axis='index')
    .set_properties(**{
        'font-size': '14px',
        'font-weight': 'bold',
        'text-align': 'left',
        'border': '1px solid #E9ECEF',
        'padding': '10px 14px',
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', GEN_COLORS['primary']),
            ('color', 'white'),
            ('font-size', '15px'),
            ('font-weight', 'bold'),
            ('text-align', 'left'),
            ('padding', '10px 14px'),
        ]},
        {'selector': 'caption', 'props': [
            ('font-size', '24px'),
            ('font-weight', 'bold'),
            ('color', GEN_COLORS['dark_text']),
            ('text-align', 'left'),
            ('padding-bottom', '14px'),
        ]},
    ])
    .set_caption("Attrition Analysis Summary")
    .applymap(_signal_color, subset=['Signal'])
)

display(styled)

# ---------------------------------------------------------------------------
# Action items
# ---------------------------------------------------------------------------
print("\n" + "=" * 80)
print("  RECOMMENDED ACTIONS")
print("=" * 80)

actions = [
    f"IMMEDIATE: Outreach to top 100 declining high-balance members "
    f"({_at_risk_count:,} total at-risk)",
]

if 'last_12mo_spend' in attrition_df.columns:
    actions.append(
        f"REVENUE PROTECTION: {gen_fmt_dollar(_spend_at_risk, None)} in annual spend at risk -- "
        f"targeted retention campaigns for declining tier"
    )

# Product bundling
if 'prod_desc' in attrition_df.columns or 'prod_code' in attrition_df.columns:
    actions.append(
        "PRODUCT STRATEGY: Evaluate product bundling for single-product declining members "
        "to increase engagement touchpoints"
    )

# Competitor win-back
if 'competitor_category' in combined_df.columns:
    actions.append(
        f"COMPETITIVE RESPONSE: Win-back offers for {len(_overlap):,} at-risk accounts "
        f"showing competitor activity ({_comp_pct:.0f}% of at-risk)"
    )

# Early warning
actions.append(
    "EARLY WARNING: Implement automated monitoring for accounts crossing 0.8x velocity "
    "threshold -- intervene before dormancy"
)

# Growth protection
actions.append(
    f"GROWTH PROTECTION: Recognize and reward {_growing_count:,} growing accounts "
    f"({_growing_pct:.1f}%) to sustain momentum"
)

for i, action in enumerate(actions, 1):
    print(f"  {i}. {action}")

print("=" * 80)
print(f"\n    Full at-risk account list available in: attrition_df[attrition_df['risk_tier'].isin(['Declining', 'Dormant'])]")
