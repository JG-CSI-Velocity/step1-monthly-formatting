# ===========================================================================
# RETENTION ACTION SUMMARY: Findings & Recommendations (Conference Edition)
# ===========================================================================
# Conference-styled findings table + strategic action items.

if 'retention_df' not in dir() or len(retention_df) == 0:
    print("    No retention data available. Skipping action summary.")
else:
    findings = []
    _total = len(retention_df)

    # -----------------------------------------------------------------------
    # 1. Overall churn/attrition rate
    # -----------------------------------------------------------------------
    _closed = (retention_df['health_status'] == 'Closed').sum()
    _closed_pct = _closed / _total * 100 if _total > 0 else 0
    findings.append({
        'Category': 'Churn Rate',
        'Finding': f"{_closed_pct:.1f}% of accounts are closed ({_closed:,} accounts)",
        'Implication': 'Baseline attrition metric for retention program ROI',
        'Priority': 'High' if _closed_pct > 5 else 'Medium',
    })

    # -----------------------------------------------------------------------
    # 2. At-risk pipeline
    # -----------------------------------------------------------------------
    _at_risk = retention_df['health_status'].isin(['Declining', 'Cooling', 'Dormant']).sum()
    _at_risk_pct = _at_risk / _total * 100 if _total > 0 else 0
    findings.append({
        'Category': 'At-Risk Pipeline',
        'Finding': f"{_at_risk:,} accounts ({_at_risk_pct:.1f}%) showing disengagement signals",
        'Implication': 'Proactive intervention window before full dormancy/closure',
        'Priority': 'High' if _at_risk_pct > 15 else 'Medium',
    })

    # -----------------------------------------------------------------------
    # 3. Attrition cost
    # -----------------------------------------------------------------------
    _closed_df = retention_df[retention_df['health_status'] == 'Closed']
    _attrition_rev = _closed_df['pre_close_monthly_spend'].sum() * 12
    findings.append({
        'Category': 'Attrition Cost',
        'Finding': f"${_attrition_rev:,.0f} annualized spend lost from closed accounts",
        'Implication': 'Quantifies the business case for retention investment',
        'Priority': 'High',
    })

    # -----------------------------------------------------------------------
    # 4. Dormancy depth
    # -----------------------------------------------------------------------
    _dormant = (retention_df['health_status'] == 'Dormant').sum()
    _dormant_pct = _dormant / _total * 100 if _total > 0 else 0
    findings.append({
        'Category': 'Dormancy',
        'Finding': f"{_dormant:,} accounts ({_dormant_pct:.1f}%) with 3+ months zero activity",
        'Implication': 'Reactivation campaigns needed -- longer dormancy = lower recovery chance',
        'Priority': 'Medium',
    })

    # -----------------------------------------------------------------------
    # 5. Engagement tier attrition
    # -----------------------------------------------------------------------
    if retention_df['engagement_tier'].nunique() > 1:
        for _tier in ['Power', 'Heavy']:
            _tier_df = retention_df[retention_df['engagement_tier'] == _tier]
            if len(_tier_df) > 0:
                _tier_at_risk = _tier_df['health_status'].isin(['Declining', 'Cooling', 'Dormant', 'Closed']).sum()
                _tier_risk_pct = _tier_at_risk / len(_tier_df) * 100
                if _tier_risk_pct > 5:
                    findings.append({
                        'Category': f'{_tier} Tier Risk',
                        'Finding': f"{_tier_risk_pct:.1f}% of {_tier} accounts are at-risk or closed",
                        'Implication': f"High-value {_tier.lower()} members disengaging -- highest retention priority",
                        'Priority': 'High',
                    })

    # -----------------------------------------------------------------------
    # Display findings table
    # -----------------------------------------------------------------------
    _findings_df = pd.DataFrame(findings)

    _priority_colors = {
        'High': f'background-color: {GEN_COLORS["accent"]}; color: white; font-weight: bold',
        'Medium': f'background-color: {GEN_COLORS["warning"]}; color: white; font-weight: bold',
        'Low': f'background-color: {GEN_COLORS["success"]}; color: white; font-weight: bold',
    }

    def _style_priority(val):
        return _priority_colors.get(val, '')

    _styled = (_findings_df.style
        .applymap(_style_priority, subset=['Priority'])
        .set_properties(**{
            'text-align': 'left',
            'font-size': '13px',
            'padding': '8px',
            'border': f'1px solid {GEN_COLORS["grid"]}',
        })
        .set_table_styles([
            {'selector': 'th', 'props': [
                ('background-color', GEN_COLORS['primary']),
                ('color', 'white'),
                ('font-weight', 'bold'),
                ('font-size', '14px'),
                ('padding', '10px'),
                ('text-align', 'left'),
            ]},
            {'selector': 'caption', 'props': [
                ('font-size', '22px'),
                ('font-weight', 'bold'),
                ('color', GEN_COLORS['dark_text']),
                ('text-align', 'left'),
                ('padding-bottom', '12px'),
            ]},
        ])
        .set_caption("Retention & Churn -- Key Findings")
        .hide(axis='index')
    )
    display(_styled)

    # -----------------------------------------------------------------------
    # Recommended actions
    # -----------------------------------------------------------------------
    print("\n  RECOMMENDED ACTIONS:")
    print("  " + "-" * 60)
    print("  1. Launch early warning system for declining Power/Heavy accounts")
    print("  2. Create dormant reactivation campaign (3+ months inactive)")
    print("  3. Build retention trigger for accounts crossing spending threshold")
    print("  4. Quantify retention ROI: cost to save vs. lifetime value lost")
    print("  5. Monitor monthly churn dashboard for trend acceleration")
