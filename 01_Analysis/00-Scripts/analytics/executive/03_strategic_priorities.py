# ===========================================================================
# STRATEGIC PRIORITIES: Top 5 Actions Ranked by Estimated Dollar Impact
# ===========================================================================
# Analyzes Red/Amber RAG areas from scorecard_df and ranks them by
# potential revenue or deposit impact. Presented as a styled HTML table.

if 'scorecard_df' not in dir() or len(scorecard_df) == 0:
    print("    scorecard_df not available -- run 01_scorecard_data first")
else:
    # -------------------------------------------------------------------
    # Build priority list from scorecard data and upstream dataframes
    # -------------------------------------------------------------------
    _priorities = []

    # Priority 1: At-risk account retention (Attrition)
    if 'attrition_df' in dir() and len(attrition_df) > 0:
        _at_risk_ct = len(attrition_df[
            attrition_df['risk_tier'].isin(['Declining', 'Dormant'])
        ])
        _spend_at_risk = 0
        if 'last_12mo_spend' in attrition_df.columns:
            _spend_at_risk = attrition_df[
                attrition_df['risk_tier'].isin(['Declining', 'Dormant'])
            ]['last_12mo_spend'].sum()
        # Assume 30% retention lift from targeted campaigns
        _retention_impact = _spend_at_risk * 0.30

        _at_risk_pct = (_at_risk_ct / len(attrition_df) * 100) if len(attrition_df) > 0 else 0
        _priorities.append({
            'priority': 1,
            'area': 'Attrition / Retention',
            'current_state': f"{_at_risk_pct:.0f}% at risk ({_at_risk_ct:,} accounts)",
            'target_state': f"Reduce at-risk by 30% within 6 months",
            'impact': _retention_impact,
            'impact_display': gen_fmt_dollar(_retention_impact, None),
            'owner': 'Member Experience / Retention Team',
        })

    # Priority 2: Cross-sell single-product members (Relationship)
    if 'rel_df' in dir() and len(rel_df) > 0 and 'product_count' in rel_df.columns:
        _single_ct = (rel_df['product_count'] == 1).sum()
        _single_pct = (_single_ct / len(rel_df) * 100) if len(rel_df) > 0 else 0
        # Assume cross-sell to 2 products increases avg balance by $2,000
        _crosssell_impact = _single_ct * 0.15 * 2000
        _priorities.append({
            'priority': 2,
            'area': 'Relationship / Cross-Sell',
            'current_state': f"{_single_pct:.0f}% single-product ({_single_ct:,} members)",
            'target_state': f"Convert 15% of single-product to 2+ products",
            'impact': _crosssell_impact,
            'impact_display': gen_fmt_dollar(_crosssell_impact, None),
            'owner': 'Product / Sales Team',
        })

    # Priority 3: Interchange optimization (PIN-to-SIG)
    if 'interchange_df' in dir() and len(interchange_df) > 0:
        _opp_total = interchange_df['opportunity'].sum() if 'opportunity' in interchange_df.columns else 0
        _num_months_ic = len(MONTH_LABELS) if 'MONTH_LABELS' in dir() else 12
        _ann_opp = _opp_total * (12.0 / _num_months_ic if _num_months_ic > 0 else 1.0)
        # Assume 40% of opportunity is capturable
        _ic_impact = _ann_opp * 0.40

        _total_pin_d = interchange_df['total_pin_dollars'].sum() if 'total_pin_dollars' in interchange_df.columns else 0
        _total_sig_d = interchange_df['total_sig_dollars'].sum() if 'total_sig_dollars' in interchange_df.columns else 0
        _sig_ratio = (_total_sig_d / (_total_pin_d + _total_sig_d) * 100) if (_total_pin_d + _total_sig_d) > 0 else 0

        _priorities.append({
            'priority': 3,
            'area': 'Interchange Optimization',
            'current_state': f"{_sig_ratio:.0f}% SIG ratio, "
                             f"{gen_fmt_dollar(_ann_opp, None)} annual gap",
            'target_state': f"Shift SIG ratio to {min(_sig_ratio + 10, 85):.0f}%",
            'impact': _ic_impact,
            'impact_display': gen_fmt_dollar(_ic_impact, None),
            'owner': 'Payments / Card Strategy',
        })

    # Priority 4: PFI growth (Payroll)
    if 'payroll_df' in dir() and len(payroll_df) > 0 and 'pfi_tier' in payroll_df.columns:
        _secondary_ct = len(payroll_df[payroll_df['pfi_tier'] == 'Secondary'])
        _tertiary_ct = len(payroll_df[payroll_df['pfi_tier'] == 'Tertiary'])
        _migration_pool = _secondary_ct + _tertiary_ct
        # Assume migrating 10% from Secondary/Tertiary to Primary adds $5,000 avg balance each
        _pfi_impact = _migration_pool * 0.10 * 5000 * 0.03  # 3% NIM on new deposits

        _payroll_pct = (payroll_df['has_payroll'].sum() / len(payroll_df) * 100) if len(payroll_df) > 0 else 0
        _priorities.append({
            'priority': 4,
            'area': 'PFI / Payroll Deepening',
            'current_state': f"{_payroll_pct:.0f}% payroll detected, "
                             f"{_migration_pool:,} in Secondary+Tertiary tier",
            'target_state': f"Migrate 10% of non-Primary to Primary PFI",
            'impact': _pfi_impact,
            'impact_display': gen_fmt_dollar(_pfi_impact, None),
            'owner': 'Deposit Strategy / Operations',
        })

    # Priority 5: Reg E optimization
    if 'rege_df' in dir() and len(rege_df) > 0:
        _opted_in = len(rege_df[rege_df['current_status'] == 'Opted-In'])
        _opted_out = len(rege_df[rege_df['current_status'] == 'Opted-Out'])
        _optin_rate = (_opted_in / len(rege_df) * 100) if len(rege_df) > 0 else 0
        _avg_od = rege_df.loc[
            rege_df['current_status'] == 'Opted-In', 'current_od_limit'
        ].mean() if 'current_od_limit' in rege_df.columns else 0
        _avg_od = _avg_od if pd.notna(_avg_od) else 0
        # Assume each opt-in generates ~$50/year in OD fee revenue
        _rege_impact = _opted_out * 0.10 * 50

        _priorities.append({
            'priority': 5,
            'area': 'Reg E / Overdraft',
            'current_state': f"{_optin_rate:.0f}% opt-in rate, "
                             f"{gen_fmt_dollar(_avg_od, None)} avg OD limit",
            'target_state': f"Convert 10% of opted-out to opt-in",
            'impact': _rege_impact,
            'impact_display': gen_fmt_dollar(_rege_impact, None),
            'owner': 'Compliance / Branch Operations',
        })

    # -------------------------------------------------------------------
    # Sort by impact (descending) and re-number
    # -------------------------------------------------------------------
    _priorities.sort(key=lambda x: x['impact'], reverse=True)
    for i, p in enumerate(_priorities):
        p['priority'] = i + 1

    # -------------------------------------------------------------------
    # Build display DataFrame
    # -------------------------------------------------------------------
    priorities_df = pd.DataFrame(_priorities[:5])  # Top 5 only

    if len(priorities_df) > 0:
        _display = priorities_df[[
            'priority', 'area', 'current_state', 'target_state',
            'impact_display', 'owner'
        ]].copy()
        _display.columns = [
            'Priority', 'Area', 'Current State', 'Target State',
            'Estimated Impact', 'Owner / Action'
        ]

        # Impact color: higher impact = bolder color
        def _impact_color(val):
            return f"color: {GEN_COLORS['accent']}; font-weight: bold"

        def _priority_color(val):
            if val == 1:
                return f"background-color: {GEN_COLORS['accent']}; color: white; font-weight: bold"
            elif val == 2:
                return f"background-color: {GEN_COLORS['warning']}; color: white; font-weight: bold"
            elif val == 3:
                return f"background-color: {GEN_COLORS['info']}; color: white; font-weight: bold"
            return f"font-weight: bold"

        styled = (
            _display.style
            .hide(axis='index')
            .set_properties(**{
                'font-size': '13px',
                'font-weight': 'bold',
                'text-align': 'left',
                'border': '1px solid #E9ECEF',
                'padding': '12px 14px',
                'vertical-align': 'top',
            })
            .set_table_styles([
                {'selector': 'th', 'props': [
                    ('background-color', GEN_COLORS['primary']),
                    ('color', 'white'),
                    ('font-size', '14px'),
                    ('font-weight', 'bold'),
                    ('text-align', 'left'),
                    ('padding', '12px 14px'),
                ]},
                {'selector': 'caption', 'props': [
                    ('font-size', '24px'),
                    ('font-weight', 'bold'),
                    ('color', GEN_COLORS['dark_text']),
                    ('text-align', 'left'),
                    ('padding-bottom', '14px'),
                ]},
                {'selector': 'table', 'props': [
                    ('width', '100%'),
                ]},
            ])
            .set_caption("Top 5 Strategic Priorities by Estimated Impact")
            .applymap(_impact_color, subset=['Estimated Impact'])
            .applymap(_priority_color, subset=['Priority'])
        )

        display(styled)

        # ---------------------------------------------------------------
        # Summary
        # ---------------------------------------------------------------
        _total_impact = priorities_df['impact'].sum()
        print(f"\n{'='*70}")
        print(f"  STRATEGIC PRIORITIES SUMMARY")
        print(f"{'='*70}")
        print(f"  Combined estimated impact: {gen_fmt_dollar(_total_impact, None)}")
        for _, row in priorities_df.iterrows():
            print(f"    {row['priority']}. {row['area']}: {row['impact_display']}")
        print(f"{'='*70}")

        print(f"\n    INSIGHT: Priorities are ranked by estimated financial impact. "
              f"The top priority alone represents "
              f"{gen_fmt_dollar(priorities_df.iloc[0]['impact'], None)} in potential value.")

    else:
        print("    No strategic priorities could be computed -- insufficient upstream data")
