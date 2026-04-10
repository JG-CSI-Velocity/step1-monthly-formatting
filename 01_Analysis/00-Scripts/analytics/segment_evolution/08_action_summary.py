# ===========================================================================
# SEGMENT EVOLUTION ACTION SUMMARY (Conference Edition)
# ===========================================================================
# Findings table + strategic action items.

if 'seg_evo_df' not in dir() or len(seg_evo_df) == 0:
    print("    No segment evolution data available. Skipping action summary.")
else:
    with_data = seg_evo_df[seg_evo_df['waves_present'] > 0]
    n_total = len(with_data)

    if n_total == 0:
        print("    No accounts with segmentation data. Skipping action summary.")
    else:
        upgraded_ct = (with_data['direction'] == 'upgraded').sum()
        degraded_ct = (with_data['direction'] == 'degraded').sum()
        stable_ct = (with_data['direction'] == 'stable').sum()

        pct_upgraded = upgraded_ct / n_total * 100
        pct_degraded = degraded_ct / n_total * 100
        pct_stable = stable_ct / n_total * 100
        upgrade_degrade_ratio = upgraded_ct / max(degraded_ct, 1)

        # ------------------------------------------------------------------
        # Portfolio health assessment
        # ------------------------------------------------------------------
        if upgrade_degrade_ratio >= 2.0:
            _health_label = "Strong"
            _health_priority = "Low"
        elif upgrade_degrade_ratio >= 1.0:
            _health_label = "Moderate"
            _health_priority = "Medium"
        else:
            _health_label = "At Risk"
            _health_priority = "High"

        findings = []

        # ------------------------------------------------------------------
        # 1. Portfolio momentum
        # ------------------------------------------------------------------
        findings.append({
            'Category': 'Portfolio Health',
            'Finding': f"{_health_label}: upgrade-to-degrade ratio {upgrade_degrade_ratio:.1f}:1",
            'Implication': f"Upgraded {pct_upgraded:.1f}% | Degraded {pct_degraded:.1f}% | Stable {pct_stable:.1f}%",
            'Priority': _health_priority,
        })

        # ------------------------------------------------------------------
        # 2. Campaign effectiveness (if available)
        # ------------------------------------------------------------------
        if 'camp_acct' in dir() and len(camp_acct) > 0:
            _camp_map = camp_acct.set_index('primary_account_num')['camp_status'].to_dict()
            _acct_col = 'Acct Number' if 'Acct Number' in with_data.columns else ' Acct Number'
            _status = pd.Series(
                with_data[_acct_col].astype(str).str.strip().map(_camp_map),
                index=with_data.index,
            )
            _resp_mask = _status == 'Responder'
            _nonresp_mask = _status == 'Non-Responder'

            if _resp_mask.sum() > 0 and _nonresp_mask.sum() > 0:
                _resp_up = (with_data.loc[_resp_mask, 'direction'] == 'upgraded').mean() * 100
                _nonresp_up = (with_data.loc[_nonresp_mask, 'direction'] == 'upgraded').mean() * 100
                _diff = _resp_up - _nonresp_up

                findings.append({
                    'Category': 'Campaign Effect',
                    'Finding': f"Responder upgrade rate {_resp_up:.1f}% vs Non-Resp {_nonresp_up:.1f}% ({_diff:+.1f}pp)",
                    'Implication': 'Campaigns show positive ROI for segment improvement' if _diff > 0 else 'Campaign impact on segment migration not clearly positive',
                    'Priority': 'Medium',
                })

        # ------------------------------------------------------------------
        # 3. Segment-level degradation risk
        # ------------------------------------------------------------------
        if 'SEG_ORDER' in dir():
            for seg in SEG_ORDER:
                _seg_accts = with_data[with_data['first_segment'] == seg]
                _n_seg = len(_seg_accts)
                if _n_seg < 10:
                    continue
                _n_deg = (_seg_accts['direction'] == 'degraded').sum()
                _deg_rate = _n_deg / _n_seg * 100
                if _deg_rate > 20:
                    findings.append({
                        'Category': f'Segment: {seg}',
                        'Finding': f"{_deg_rate:.1f}% degradation rate ({_n_deg:,} of {_n_seg:,})",
                        'Implication': 'High degradation -- target for retention intervention',
                        'Priority': 'High' if _deg_rate > 30 else 'Medium',
                    })

        # ------------------------------------------------------------------
        # 4. Segment risk table
        # ------------------------------------------------------------------
        seg_risk_rows = []
        for seg in SEG_ORDER:
            _seg_accts = with_data[with_data['first_segment'] == seg]
            _n_seg = len(_seg_accts)
            if _n_seg == 0:
                continue
            _n_deg = (_seg_accts['direction'] == 'degraded').sum()
            _n_upg = (_seg_accts['direction'] == 'upgraded').sum()
            seg_risk_rows.append({
                'Segment': seg,
                'Accounts': _n_seg,
                'Upgrade %': _n_upg / _n_seg * 100,
                'Degrade %': _n_deg / _n_seg * 100,
                'Net Flow': (_n_upg - _n_deg) / _n_seg * 100,
            })

        seg_risk_df = pd.DataFrame(seg_risk_rows)

        # ------------------------------------------------------------------
        # Display findings table
        # ------------------------------------------------------------------
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
            .set_caption("Segment Evolution -- Key Findings")
            .hide(axis='index')
        )
        display(_styled)

        # ------------------------------------------------------------------
        # Segment risk table
        # ------------------------------------------------------------------
        if len(seg_risk_df) > 0:
            _styled_risk = (
                seg_risk_df.style
                .hide(axis='index')
                .format({
                    'Accounts': '{:,}',
                    'Upgrade %': '{:.1f}%',
                    'Degrade %': '{:.1f}%',
                    'Net Flow': '{:+.1f}pp',
                })
                .background_gradient(
                    subset=['Net Flow'],
                    cmap='RdYlGn',
                    vmin=-30, vmax=30,
                )
                .set_properties(**{
                    'font-size': '13px', 'font-weight': 'bold',
                    'text-align': 'center',
                    'border': f'1px solid {GEN_COLORS["grid"]}',
                    'padding': '7px 10px',
                })
                .set_table_styles([
                    {'selector': 'th', 'props': [
                        ('background-color', GEN_COLORS['warning']),
                        ('color', 'white'), ('font-size', '14px'),
                        ('font-weight', 'bold'), ('text-align', 'center'),
                        ('padding', '8px 10px'),
                    ]},
                    {'selector': 'caption', 'props': [
                        ('font-size', '18px'), ('font-weight', 'bold'),
                        ('color', GEN_COLORS['dark_text']),
                        ('text-align', 'left'),
                        ('padding-bottom', '10px'),
                    ]},
                ])
                .set_caption("Segment-Level Migration Rates")
            )
            display(_styled_risk)

        # ------------------------------------------------------------------
        # Recommended actions
        # ------------------------------------------------------------------
        print("\n  RECOMMENDED INTERVENTIONS:")
        print("  " + "-" * 60)
        print("  1. Bottom-segment watch list: proactive outreach with")
        print("     personalized offers before full disengagement")
        print("  2. Recently degraded accounts: win-back campaign with")
        print("     balance transfer incentives or relationship review")
        print("  3. Stable middle-segment: cross-sell additional products,")
        print("     nudge toward next tier with rewards")
        print("  4. Top-segment retention: exclusive benefits and referral")
        print("     incentives to protect highest-value members")
        print("  5. Track upgrade-to-degrade ratio monthly; escalate if < 1.0")

        print(f"\n    Segment Evolution analysis complete.")
        print(f"    Portfolio health: {_health_label} "
              f"(upgrade:degrade = {upgrade_degrade_ratio:.1f}:1)")
        print(f"    Total accounts analyzed: {n_total:,}")
