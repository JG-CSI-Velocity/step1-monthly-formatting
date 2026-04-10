# ===========================================================================
# BALANCE ACTION SUMMARY: Findings & Recommendations (Conference Edition)
# ===========================================================================
# Conference-styled findings table + strategic action items.

findings = []

# ---------------------------------------------------------------------------
# 1. Deposit concentration
# ---------------------------------------------------------------------------
if 'Curr Bal' in balance_df.columns:
    positive_bals = balance_df[balance_df['Curr Bal'] > 0]['Curr Bal']
    if len(positive_bals) > 0:
        top_10_thresh = positive_bals.quantile(0.90)
        top_10_dep = positive_bals[positive_bals >= top_10_thresh].sum()
        top_10_dep_pct = top_10_dep / positive_bals.sum() * 100

        findings.append({
            'Category': 'Concentration Risk',
            'Finding': (f"Top 10% of depositors hold {top_10_dep_pct:.0f}% of all deposits "
                        f"(threshold: {gen_fmt_dollar(top_10_thresh, None)})"),
            'Implication': 'Heavy reliance on small depositor base -- retention is critical',
            'Priority': 'High' if top_10_dep_pct > 60 else 'Medium'
        })

# ---------------------------------------------------------------------------
# 2. Sleeping giants
# ---------------------------------------------------------------------------
if 'Avg Bal' in balance_df.columns and 'total_spend' in balance_df.columns:
    active_df = balance_df[(balance_df['Avg Bal'] > 0) & (balance_df['total_spend'] > 0)]
    if len(active_df) > 0:
        med_bal_f = active_df['Avg Bal'].median()
        med_spend_f = active_df['total_spend'].median()
        giants = active_df[
            (active_df['Avg Bal'] >= med_bal_f) & (active_df['total_spend'] < med_spend_f)
        ]
        giants_deposits = giants['Avg Bal'].sum()

        findings.append({
            'Category': 'Sleeping Giants',
            'Finding': (f"{len(giants):,} accounts with high balance but low card usage "
                        f"({gen_fmt_dollar(giants_deposits, None)} in deposits)"),
            'Implication': 'Cross-sell card products, rewards, and payment solutions',
            'Priority': 'High'
        })

# ---------------------------------------------------------------------------
# 3. Deposit flight risk
# ---------------------------------------------------------------------------
if 'bal_delta' in balance_df.columns:
    high_risk = balance_df[
        (balance_df['Curr Bal'] >= 25_000) & (balance_df['bal_delta'] < 0)
    ]
    if len(high_risk) > 0:
        risk_deposits = high_risk['Curr Bal'].sum()
        risk_decline = high_risk['bal_delta'].abs().sum()

        findings.append({
            'Category': 'Deposit Flight Risk',
            'Finding': (f"{len(high_risk):,} high-balance accounts ($25K+) with declining deposits -- "
                        f"{gen_fmt_dollar(risk_deposits, None)} at risk, "
                        f"{gen_fmt_dollar(risk_decline, None)} already declined"),
            'Implication': 'Proactive outreach needed; potential attrition signal',
            'Priority': 'High'
        })

# ---------------------------------------------------------------------------
# 4. PFI distribution
# ---------------------------------------------------------------------------
if 'pfi_tier' in pfi_df.columns:
    pfi_counts = pfi_df['pfi_tier'].value_counts()
    total_pfi = pfi_counts.sum()
    primary_n = pfi_counts.get('Primary', 0)
    incidental_n = pfi_counts.get('Incidental', 0)
    primary_pct_f = primary_n / total_pfi * 100 if total_pfi > 0 else 0
    incidental_pct_f = incidental_n / total_pfi * 100 if total_pfi > 0 else 0

    findings.append({
        'Category': 'PFI Scoring',
        'Finding': (f"{primary_pct_f:.1f}% Primary FI, {incidental_pct_f:.1f}% Incidental -- "
                    f"{incidental_n:,} members barely engaged"),
        'Implication': 'Upgrade Incidental/Tertiary members via targeted product bundling',
        'Priority': 'High' if incidental_pct_f > 30 else 'Medium'
    })

# ---------------------------------------------------------------------------
# 5. Zero-balance accounts
# ---------------------------------------------------------------------------
findings.append({
    'Category': 'Zero Balances',
    'Finding': (f"{zero_bal_count:,} accounts ({zero_bal_pct:.1f}%) "
                f"carry zero balance"),
    'Implication': 'Reactivation campaign opportunity -- direct deposit, savings challenges',
    'Priority': 'Medium' if zero_bal_pct < 20 else 'High'
})

# ---------------------------------------------------------------------------
# 6. Competitor leakage (if available)
# ---------------------------------------------------------------------------
if 'competitor_spend_pct' in balance_df.columns:
    high_bal_comp = balance_df[
        (balance_df['Avg Bal'] >= 10_000) &
        (balance_df['competitor_spend_pct'] >= 30)
    ]
    if len(high_bal_comp) > 0:
        findings.append({
            'Category': 'Competitor Leakage',
            'Finding': (f"{len(high_bal_comp):,} high-balance members send 30%+ of spend "
                        f"to competitors ({gen_fmt_dollar(high_bal_comp['Avg Bal'].sum(), None)} "
                        f"in deposits)"),
            'Implication': 'Best depositors using competitor cards -- activate with rewards',
            'Priority': 'High'
        })

# ---------------------------------------------------------------------------
# Styled findings table
# ---------------------------------------------------------------------------
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
    .set_caption("Balance Analysis: Key Findings & Recommendations")
)

display(styled_findings)

# ---------------------------------------------------------------------------
# Strategic action items
# ---------------------------------------------------------------------------
actions = [
    "Implement deposit retention program for top 10% depositors -- proactive outreach",
    "Activate Sleeping Giants with card rewards and payment product campaigns",
    "Build early-warning system for deposit flight risk (declining bal_delta)",
    "Launch PFI upgrade journeys: Incidental -> Tertiary -> Secondary -> Primary",
    f"Reactivate {zero_bal_count:,} zero-balance accounts via direct deposit incentives",
    "Cross-reference competitor activity with balance data for targeted win-back",
]

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
        'font-weight': 'bold', 'color': GEN_COLORS['accent'],
        'text-align': 'center',
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', GEN_COLORS['accent']),
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
    .set_caption("Balance Portfolio: Strategic Action Items")
)

display(styled_actions)

print(f"\n    Balance analysis complete. {len(findings)} key findings identified.")
