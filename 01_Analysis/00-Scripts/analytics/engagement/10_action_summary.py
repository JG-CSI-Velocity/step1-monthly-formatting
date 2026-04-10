# ===========================================================================
# ENGAGEMENT MIGRATION ACTION SUMMARY (Conference Edition)
# ===========================================================================
# Findings table + strategic action items.

if 'migration_summary' not in dir() or not isinstance(migration_summary, pd.DataFrame) or len(migration_summary) == 0:
    print("    No migration data available. Skipping action summary.")
else:
    findings = []

    # -----------------------------------------------------------------------
    # 1. Overall direction
    # -----------------------------------------------------------------------
    _total_start = migration_summary['start_count'].sum()
    _net_overall = monthly_transitions['net_migration'].mean() if len(monthly_transitions) > 0 else 0
    _direction = "upgrading" if _net_overall > 0 else "downgrading"

    findings.append({
        'Category': 'Portfolio Momentum',
        'Finding': f"Net {_direction}: avg {abs(_net_overall):,.0f} accounts/month",
        'Implication': f"Portfolio engagement is {'improving' if _net_overall > 0 else 'eroding'} over time",
        'Priority': 'High' if _net_overall < 0 else 'Low',
    })

    # -----------------------------------------------------------------------
    # 2. Power tier growth
    # -----------------------------------------------------------------------
    _power = migration_summary[migration_summary['tier'] == 'Power']
    if len(_power) > 0:
        _pn = _power.iloc[0]
        findings.append({
            'Category': 'Power Tier',
            'Finding': f"Power accounts: {_pn['start_count']:,} -> {_pn['end_count']:,} ({_pn['net_pct']:+.1f}%)",
            'Implication': f"{'Growing' if _pn['net_change'] > 0 else 'Shrinking'} high-value base",
            'Priority': 'High' if _pn['net_change'] < 0 else 'Low',
        })

    # -----------------------------------------------------------------------
    # 3. Dormant growth
    # -----------------------------------------------------------------------
    _dormant = migration_summary[migration_summary['tier'] == 'Dormant']
    if len(_dormant) > 0:
        _dn = _dormant.iloc[0]
        findings.append({
            'Category': 'Dormant Growth',
            'Finding': f"Dormant accounts: {_dn['start_count']:,} -> {_dn['end_count']:,} ({_dn['net_pct']:+.1f}%)",
            'Implication': f"{'Expanding' if _dn['net_change'] > 0 else 'Shrinking'} disengaged population",
            'Priority': 'High' if _dn['net_change'] > 0 else 'Low',
        })

    # -----------------------------------------------------------------------
    # 4. Stability rate
    # -----------------------------------------------------------------------
    _avg_stability = monthly_transitions['stability_rate'].mean()
    findings.append({
        'Category': 'Tier Stability',
        'Finding': f"{_avg_stability:.0f}% of accounts stay in the same tier month-over-month",
        'Implication': 'High stability may indicate entrenched behavior patterns',
        'Priority': 'Medium',
    })

    # -----------------------------------------------------------------------
    # 5. Campaign impact on migration (if available)
    # -----------------------------------------------------------------------
    if 'camp_acct' in dir() and len(camp_acct) > 0 and 'migration_tier_df' in dir():
        _camp_map = camp_acct.set_index('primary_account_num')['camp_status'].to_dict()
        _tier_rank = {'Power': 0, 'Heavy': 1, 'Moderate': 2, 'Light': 3, 'Dormant': 4}

        _first_m = migration_tier_df.columns[0]
        _last_m = migration_tier_df.columns[-1]

        for _status in ['Responder', 'Non-Responder']:
            _mask = pd.Series(migration_tier_df.index.map(lambda x: _camp_map.get(x) == _status), index=migration_tier_df.index)
            if _mask.sum() > 0:
                _from = migration_tier_df.loc[_mask, _first_m].map(_tier_rank)
                _to = migration_tier_df.loc[_mask, _last_m].map(_tier_rank)
                _up = (_to < _from).sum()
                _down = (_to > _from).sum()
                _net_rate = (_up - _down) / _mask.sum() * 100

                if _status == 'Responder':
                    findings.append({
                        'Category': 'Campaign Effect',
                        'Finding': f"Responders: {_net_rate:+.1f}% net migration rate vs portfolio",
                        'Implication': 'Campaign may be driving engagement improvement' if _net_rate > 0 else 'Responders still declining despite campaign',
                        'Priority': 'Medium',
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
        .set_caption("Engagement Migration -- Key Findings")
        .hide(axis='index')
    )
    display(_styled)

    print("\n  RECOMMENDED ACTIONS:")
    print("  " + "-" * 60)
    print("  1. Target Moderate->Heavy upgrade path with incentive campaigns")
    print("  2. Monitor Power tier for early signs of disengagement")
    print("  3. Create reactivation trigger for accounts crossing Light->Dormant")
    print("  4. Measure campaign impact on engagement migration rates")
    print("  5. Build quarterly migration report for board presentations")
