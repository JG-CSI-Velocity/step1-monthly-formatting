# ===========================================================================
# EXECUTIVE SCORECARD DATA: Pull Top KPIs from All Analysis Folders
# ===========================================================================
# Aggregates the single most important metric from each of the 7 analysis
# folders into a unified scorecard_df with RAG status and trend indicators.

# ---------------------------------------------------------------------------
# Initialize scorecard list
# ---------------------------------------------------------------------------
_scorecard_rows = []

# ---------------------------------------------------------------------------
# 1. ATTRITION KPIs
# ---------------------------------------------------------------------------
if 'attrition_df' in dir() and len(attrition_df) > 0:
    _total_attrition = len(attrition_df)

    # KPI 1: % at risk (Declining + Dormant)
    _declining = len(attrition_df[attrition_df['risk_tier'] == 'Declining'])
    _dormant = len(attrition_df[attrition_df['risk_tier'] == 'Dormant'])
    _at_risk = _declining + _dormant
    _at_risk_pct = (_at_risk / _total_attrition * 100) if _total_attrition > 0 else 0

    _rag_atr = 'Red' if _at_risk_pct > 25 else ('Amber' if _at_risk_pct > 15 else 'Green')

    # Trend: compare spend velocity of declining accounts
    _avg_vel = attrition_df[
        attrition_df['risk_tier'].isin(['Declining', 'Dormant'])
    ]['spend_velocity'].mean() if _at_risk > 0 else 1.0
    _trend_atr = 'down' if _avg_vel < 0.6 else ('flat' if _avg_vel < 0.9 else 'up')

    _scorecard_rows.append({
        'category': 'Attrition',
        'metric_name': '% Accounts At Risk',
        'value': _at_risk_pct,
        'display': f"{_at_risk_pct:.1f}%",
        'trend': _trend_atr,
        'rag': _rag_atr,
    })

    # KPI 2: $ at risk (annual spend from declining + dormant)
    if 'last_12mo_spend' in attrition_df.columns:
        _spend_at_risk = attrition_df[
            attrition_df['risk_tier'].isin(['Declining', 'Dormant'])
        ]['last_12mo_spend'].sum()
        _rag_spend = 'Red' if _spend_at_risk > 5_000_000 else (
            'Amber' if _spend_at_risk > 1_000_000 else 'Green')

        _scorecard_rows.append({
            'category': 'Attrition',
            'metric_name': 'Annual Spend at Risk',
            'value': _spend_at_risk,
            'display': gen_fmt_dollar(_spend_at_risk, None),
            'trend': _trend_atr,
            'rag': _rag_spend,
        })

    print(f"    Attrition KPIs loaded: {_at_risk_pct:.1f}% at risk, "
          f"{gen_fmt_dollar(_spend_at_risk, None) if 'last_12mo_spend' in attrition_df.columns else 'N/A'} spend at risk")
else:
    print("    Attrition data not available -- skipping attrition KPIs")

# ---------------------------------------------------------------------------
# 2. BALANCE KPIs
# ---------------------------------------------------------------------------
if 'balance_df' in dir() and len(balance_df) > 0:
    _total_bal_accts = len(balance_df)

    # KPI 3: Total deposits
    _total_deposits = balance_df['Curr Bal'].sum() if 'Curr Bal' in balance_df.columns else 0
    _rag_dep = 'Green'  # baseline metric, no threshold
    _scorecard_rows.append({
        'category': 'Balance',
        'metric_name': 'Total Deposits',
        'value': _total_deposits,
        'display': gen_fmt_dollar(_total_deposits, None),
        'trend': 'flat',
        'rag': _rag_dep,
    })

    # KPI 4: Average balance
    _avg_balance = balance_df['Curr Bal'].mean() if 'Curr Bal' in balance_df.columns else 0
    _rag_avg = 'Green' if _avg_balance > 5000 else ('Amber' if _avg_balance > 2000 else 'Red')
    _scorecard_rows.append({
        'category': 'Balance',
        'metric_name': 'Average Balance',
        'value': _avg_balance,
        'display': gen_fmt_dollar(_avg_balance, None),
        'trend': 'flat',
        'rag': _rag_avg,
    })

    # KPI 5: % zero-balance accounts
    _zero_ct = (balance_df['Curr Bal'] <= 0).sum() if 'Curr Bal' in balance_df.columns else 0
    _zero_pct = (_zero_ct / _total_bal_accts * 100) if _total_bal_accts > 0 else 0
    _rag_zero = 'Red' if _zero_pct > 20 else ('Amber' if _zero_pct > 10 else 'Green')
    _scorecard_rows.append({
        'category': 'Balance',
        'metric_name': '% Zero-Balance Accounts',
        'value': _zero_pct,
        'display': f"{_zero_pct:.1f}%",
        'trend': 'flat',
        'rag': _rag_zero,
    })

    print(f"    Balance KPIs loaded: {gen_fmt_dollar(_total_deposits, None)} deposits, "
          f"{gen_fmt_dollar(_avg_balance, None)} avg, {_zero_pct:.1f}% zero-bal")
else:
    print("    Balance data not available -- skipping balance KPIs")

# ---------------------------------------------------------------------------
# 3. INTERCHANGE KPIs
# ---------------------------------------------------------------------------
if 'interchange_df' in dir() and len(interchange_df) > 0:
    _num_months_ic = len(MONTH_LABELS) if 'MONTH_LABELS' in dir() else 12
    _ann_factor = 12.0 / _num_months_ic if _num_months_ic > 0 else 1.0

    # KPI 6: Estimated annual interchange revenue
    _total_ic = interchange_df['total_interchange'].sum() if 'total_interchange' in interchange_df.columns else 0
    _annual_ic = _total_ic * _ann_factor
    _rag_ic = 'Green'
    _scorecard_rows.append({
        'category': 'Interchange',
        'metric_name': 'Est. Annual Interchange',
        'value': _annual_ic,
        'display': gen_fmt_dollar(_annual_ic, None),
        'trend': 'flat',
        'rag': _rag_ic,
    })

    # KPI 7: SIG ratio
    _total_pin_d = interchange_df['total_pin_dollars'].sum() if 'total_pin_dollars' in interchange_df.columns else 0
    _total_sig_d = interchange_df['total_sig_dollars'].sum() if 'total_sig_dollars' in interchange_df.columns else 0
    _sig_ratio = (_total_sig_d / (_total_pin_d + _total_sig_d) * 100) if (_total_pin_d + _total_sig_d) > 0 else 0
    _rag_sig = 'Green' if _sig_ratio > 70 else ('Amber' if _sig_ratio > 50 else 'Red')

    # Trend from monthly data if available
    _ic_trend = 'flat'
    if 'monthly_interchange' in dir() and len(monthly_interchange) >= 3:
        _first_half = monthly_interchange['sig_ratio'].iloc[:len(monthly_interchange)//2].mean()
        _second_half = monthly_interchange['sig_ratio'].iloc[len(monthly_interchange)//2:].mean()
        if _second_half > _first_half * 1.02:
            _ic_trend = 'up'
        elif _second_half < _first_half * 0.98:
            _ic_trend = 'down'

    _scorecard_rows.append({
        'category': 'Interchange',
        'metric_name': 'SIG Ratio',
        'value': _sig_ratio,
        'display': f"{_sig_ratio:.1f}%",
        'trend': _ic_trend,
        'rag': _rag_sig,
    })

    # KPI 8: Revenue opportunity (PIN-to-SIG shift)
    _opp = interchange_df['opportunity'].sum() if 'opportunity' in interchange_df.columns else 0
    _annual_opp = _opp * _ann_factor
    _rag_opp = 'Amber' if _annual_opp > 50_000 else 'Green'
    _scorecard_rows.append({
        'category': 'Interchange',
        'metric_name': 'PIN-to-SIG Opportunity',
        'value': _annual_opp,
        'display': gen_fmt_dollar(_annual_opp, None),
        'trend': _ic_trend,
        'rag': _rag_opp,
    })

    print(f"    Interchange KPIs loaded: {gen_fmt_dollar(_annual_ic, None)} annual, "
          f"{_sig_ratio:.1f}% SIG ratio, {gen_fmt_dollar(_annual_opp, None)} opportunity")
else:
    print("    Interchange data not available -- skipping interchange KPIs")

# ---------------------------------------------------------------------------
# 4. REG E / OVERDRAFT KPIs
# ---------------------------------------------------------------------------
if 'rege_df' in dir() and len(rege_df) > 0:
    _total_rege = len(rege_df)

    # KPI 9: Opt-in rate
    _opted_in = len(rege_df[rege_df['current_status'] == 'Opted-In'])
    _optin_rate = (_opted_in / _total_rege * 100) if _total_rege > 0 else 0
    _rag_optin = 'Green' if _optin_rate > 40 else ('Amber' if _optin_rate > 25 else 'Red')

    # Trend: compare first vs current opt-in
    _rege_trend = 'flat'
    if 'first_status' in rege_df.columns:
        _first_optin = (rege_df['first_status'] == 'Opted-In').sum()
        _first_rate = (_first_optin / _total_rege * 100) if _total_rege > 0 else 0
        if _optin_rate > _first_rate + 1:
            _rege_trend = 'up'
        elif _optin_rate < _first_rate - 1:
            _rege_trend = 'down'

    _scorecard_rows.append({
        'category': 'Reg E',
        'metric_name': 'Opt-In Rate',
        'value': _optin_rate,
        'display': f"{_optin_rate:.1f}%",
        'trend': _rege_trend,
        'rag': _rag_optin,
    })

    # KPI 10: Avg OD limit
    _avg_od = rege_df.loc[
        rege_df['current_status'] == 'Opted-In', 'current_od_limit'
    ].mean() if 'current_od_limit' in rege_df.columns else 0
    _avg_od = _avg_od if pd.notna(_avg_od) else 0
    _rag_od = 'Green' if _avg_od > 500 else ('Amber' if _avg_od > 200 else 'Red')
    _scorecard_rows.append({
        'category': 'Reg E',
        'metric_name': 'Avg OD Limit (Opted-In)',
        'value': _avg_od,
        'display': gen_fmt_dollar(_avg_od, None),
        'trend': 'flat',
        'rag': _rag_od,
    })

    print(f"    Reg E KPIs loaded: {_optin_rate:.1f}% opt-in, "
          f"{gen_fmt_dollar(_avg_od, None)} avg OD limit")
else:
    print("    Reg E data not available -- skipping Reg E KPIs")

# ---------------------------------------------------------------------------
# 5. PAYROLL KPIs
# ---------------------------------------------------------------------------
if 'payroll_df' in dir() and len(payroll_df) > 0:
    _total_payroll = len(payroll_df)

    # KPI 11: % with detected payroll
    _has_payroll = payroll_df['has_payroll'].sum() if 'has_payroll' in payroll_df.columns else 0
    _payroll_pct = (_has_payroll / _total_payroll * 100) if _total_payroll > 0 else 0
    _rag_payroll = 'Green' if _payroll_pct > 30 else ('Amber' if _payroll_pct > 15 else 'Red')
    _scorecard_rows.append({
        'category': 'Payroll',
        'metric_name': '% With Payroll/DD',
        'value': _payroll_pct,
        'display': f"{_payroll_pct:.1f}%",
        'trend': 'flat',
        'rag': _rag_payroll,
    })

    # KPI 12: % Primary PFI tier
    _primary_pfi_pct = 0
    if 'pfi_tier' in payroll_df.columns:
        _primary_ct = len(payroll_df[payroll_df['pfi_tier'] == 'Primary'])
        _primary_pfi_pct = (_primary_ct / _total_payroll * 100) if _total_payroll > 0 else 0
    _rag_pfi = 'Green' if _primary_pfi_pct > 25 else ('Amber' if _primary_pfi_pct > 10 else 'Red')
    _scorecard_rows.append({
        'category': 'Payroll',
        'metric_name': '% Primary PFI Tier',
        'value': _primary_pfi_pct,
        'display': f"{_primary_pfi_pct:.1f}%",
        'trend': 'flat',
        'rag': _rag_pfi,
    })

    print(f"    Payroll KPIs loaded: {_payroll_pct:.1f}% with payroll, "
          f"{_primary_pfi_pct:.1f}% primary PFI")
else:
    print("    Payroll data not available -- skipping payroll KPIs")

# ---------------------------------------------------------------------------
# 6. RELATIONSHIP KPIs
# ---------------------------------------------------------------------------
if 'rel_df' in dir() and len(rel_df) > 0:
    _total_rel = len(rel_df)

    # KPI 13: Avg products per member
    _avg_prods = rel_df['product_count'].mean() if 'product_count' in rel_df.columns else 0
    _rag_prods = 'Green' if _avg_prods > 2.5 else ('Amber' if _avg_prods > 1.5 else 'Red')
    _scorecard_rows.append({
        'category': 'Relationship',
        'metric_name': 'Avg Products/Member',
        'value': _avg_prods,
        'display': f"{_avg_prods:.2f}",
        'trend': 'flat',
        'rag': _rag_prods,
    })

    # KPI 14: % single-product members
    _single_ct = (rel_df['product_count'] == 1).sum() if 'product_count' in rel_df.columns else 0
    _single_pct = (_single_ct / _total_rel * 100) if _total_rel > 0 else 0
    _rag_single = 'Red' if _single_pct > 50 else ('Amber' if _single_pct > 30 else 'Green')
    _scorecard_rows.append({
        'category': 'Relationship',
        'metric_name': '% Single-Product Members',
        'value': _single_pct,
        'display': f"{_single_pct:.1f}%",
        'trend': 'flat',
        'rag': _rag_single,
    })

    print(f"    Relationship KPIs loaded: {_avg_prods:.2f} avg products, "
          f"{_single_pct:.1f}% single-product")
else:
    print("    Relationship data not available -- skipping relationship KPIs")

# ---------------------------------------------------------------------------
# 7. SEGMENTATION KPIs
# ---------------------------------------------------------------------------
if 'seg_evo_df' in dir() and len(seg_evo_df) > 0 and 'direction' in seg_evo_df.columns:
    _total_seg = len(seg_evo_df)
    _with_data = (seg_evo_df['waves_present'] > 0).sum() if 'waves_present' in seg_evo_df.columns else _total_seg

    # KPI 15: % upgraded
    _upgraded = (seg_evo_df['direction'] == 'upgraded').sum()
    _upgraded_pct = (_upgraded / _with_data * 100) if _with_data > 0 else 0
    _rag_up = 'Green' if _upgraded_pct > 15 else ('Amber' if _upgraded_pct > 5 else 'Red')
    _scorecard_rows.append({
        'category': 'Segmentation',
        'metric_name': '% Upgraded',
        'value': _upgraded_pct,
        'display': f"{_upgraded_pct:.1f}%",
        'trend': 'up' if _upgraded_pct > 10 else 'flat',
        'rag': _rag_up,
    })

    # KPI 16: % degraded
    _degraded = (seg_evo_df['direction'] == 'degraded').sum()
    _degraded_pct = (_degraded / _with_data * 100) if _with_data > 0 else 0
    _rag_down = 'Red' if _degraded_pct > 20 else ('Amber' if _degraded_pct > 10 else 'Green')
    _scorecard_rows.append({
        'category': 'Segmentation',
        'metric_name': '% Degraded',
        'value': _degraded_pct,
        'display': f"{_degraded_pct:.1f}%",
        'trend': 'down' if _degraded_pct > 15 else 'flat',
        'rag': _rag_down,
    })

    print(f"    Segmentation KPIs loaded: {_upgraded_pct:.1f}% upgraded, "
          f"{_degraded_pct:.1f}% degraded")
else:
    print("    Segmentation data not available -- skipping segmentation KPIs")

# ---------------------------------------------------------------------------
# 8. RETENTION KPIs
# ---------------------------------------------------------------------------
if 'retention_df' in dir() and isinstance(retention_df, pd.DataFrame) and len(retention_df) > 0:
    _total_ret = len(retention_df)

    # KPI: At-risk rate (declining + cooling + dormant + closed)
    _at_risk_ct = retention_df['health_status'].isin(
        ['Declining', 'Cooling', 'Dormant', 'Closed']
    ).sum()
    _at_risk_pct = _at_risk_ct / _total_ret * 100 if _total_ret > 0 else 0
    _rag_risk = 'Red' if _at_risk_pct > 25 else ('Amber' if _at_risk_pct > 15 else 'Green')
    _scorecard_rows.append({
        'category': 'Retention',
        'metric_name': '% Accounts At Risk',
        'value': _at_risk_pct,
        'display': f"{_at_risk_pct:.1f}%",
        'trend': 'flat',
        'rag': _rag_risk,
    })

    # KPI: Closed account rate
    _closed_ct = (retention_df['health_status'] == 'Closed').sum()
    _closed_pct = _closed_ct / _total_ret * 100 if _total_ret > 0 else 0
    _rag_closed = 'Red' if _closed_pct > 10 else ('Amber' if _closed_pct > 5 else 'Green')
    _scorecard_rows.append({
        'category': 'Retention',
        'metric_name': 'Closed Account Rate',
        'value': _closed_pct,
        'display': f"{_closed_pct:.1f}%",
        'trend': 'flat',
        'rag': _rag_closed,
    })

    # KPI: Attrition spend at risk
    _atr_spend = retention_df.loc[
        retention_df['health_status'].isin(['Declining', 'Cooling', 'Dormant']),
        'last_3mo_avg_spend'
    ].sum() * 12
    _rag_atr_spend = 'Red' if _atr_spend > 5_000_000 else ('Amber' if _atr_spend > 1_000_000 else 'Green')
    _scorecard_rows.append({
        'category': 'Retention',
        'metric_name': 'Annual Spend at Risk',
        'value': _atr_spend,
        'display': gen_fmt_dollar(_atr_spend, None),
        'trend': 'flat',
        'rag': _rag_atr_spend,
    })

    print(f"    Retention KPIs loaded: {_at_risk_pct:.1f}% at risk, "
          f"{_closed_pct:.1f}% closed, {gen_fmt_dollar(_atr_spend, None)} spend at risk")
else:
    print("    Retention data not available -- skipping retention KPIs")

# ---------------------------------------------------------------------------
# 9. ENGAGEMENT MIGRATION KPIs
# ---------------------------------------------------------------------------
if 'migration_summary' in dir() and isinstance(migration_summary, pd.DataFrame) and len(migration_summary) > 0:
    # KPI: Net migration direction
    if 'monthly_transitions' in dir() and len(monthly_transitions) > 0:
        _avg_net = monthly_transitions['net_migration'].mean()
        _net_direction = 'up' if _avg_net > 0 else ('down' if _avg_net < 0 else 'flat')
        _rag_mig = 'Green' if _avg_net > 0 else ('Red' if _avg_net < -50 else 'Amber')
        _scorecard_rows.append({
            'category': 'Engagement',
            'metric_name': 'Net Migration/Month',
            'value': _avg_net,
            'display': f"{_avg_net:+,.0f}",
            'trend': _net_direction,
            'rag': _rag_mig,
        })

    # KPI: Power tier growth
    _power = migration_summary[migration_summary['tier'] == 'Power']
    if len(_power) > 0:
        _pn = _power.iloc[0]
        _power_pct = _pn['net_pct']
        _rag_power = 'Green' if _power_pct > 0 else ('Amber' if _power_pct > -5 else 'Red')
        _scorecard_rows.append({
            'category': 'Engagement',
            'metric_name': 'Power Tier Growth',
            'value': _power_pct,
            'display': f"{_power_pct:+.1f}%",
            'trend': 'up' if _power_pct > 0 else 'down',
            'rag': _rag_power,
        })

    # KPI: Dormant growth
    _dormant = migration_summary[migration_summary['tier'] == 'Dormant']
    if len(_dormant) > 0:
        _dn = _dormant.iloc[0]
        _dorm_pct = _dn['net_pct']
        _rag_dorm = 'Red' if _dorm_pct > 5 else ('Amber' if _dorm_pct > 0 else 'Green')
        _scorecard_rows.append({
            'category': 'Engagement',
            'metric_name': 'Dormant Tier Growth',
            'value': _dorm_pct,
            'display': f"{_dorm_pct:+.1f}%",
            'trend': 'up' if _dorm_pct > 0 else 'down',
            'rag': _rag_dorm,
        })

    print(f"    Engagement Migration KPIs loaded")
else:
    print("    Engagement migration data not available -- skipping migration KPIs")

# ---------------------------------------------------------------------------
# Build scorecard_df
# ---------------------------------------------------------------------------
scorecard_df = pd.DataFrame(_scorecard_rows)

# ---------------------------------------------------------------------------
# Summary table
# ---------------------------------------------------------------------------
if len(scorecard_df) > 0:
    _rag_color_map = {
        'Green': GEN_COLORS['success'],
        'Amber': GEN_COLORS['warning'],
        'Red': GEN_COLORS['accent'],
    }
    _trend_symbol = {'up': 'Up', 'down': 'Down', 'flat': 'Flat'}

    _display_df = scorecard_df[['category', 'metric_name', 'display', 'trend', 'rag']].copy()
    _display_df.columns = ['Category', 'Metric', 'Value', 'Trend', 'RAG']
    _display_df['Trend'] = _display_df['Trend'].map(_trend_symbol)

    def _rag_style(val):
        c = _rag_color_map.get(val, GEN_COLORS['dark_text'])
        return f"color: {c}; font-weight: bold"

    def _trend_style(val):
        if val == 'Up':
            return f"color: {GEN_COLORS['success']}; font-weight: bold"
        elif val == 'Down':
            return f"color: {GEN_COLORS['accent']}; font-weight: bold"
        return f"color: {GEN_COLORS['muted']}; font-weight: bold"

    styled = (
        _display_df.style
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
        .set_caption("Executive Scorecard: All KPIs")
        .applymap(_rag_style, subset=['RAG'])
        .applymap(_trend_style, subset=['Trend'])
    )

    display(styled)

# ---------------------------------------------------------------------------
# Summary counts
# ---------------------------------------------------------------------------
_n_green = (scorecard_df['rag'] == 'Green').sum() if len(scorecard_df) > 0 else 0
_n_amber = (scorecard_df['rag'] == 'Amber').sum() if len(scorecard_df) > 0 else 0
_n_red = (scorecard_df['rag'] == 'Red').sum() if len(scorecard_df) > 0 else 0

print(f"\n{'='*60}")
print(f"  EXECUTIVE SCORECARD SUMMARY")
print(f"{'='*60}")
print(f"  Total KPIs tracked: {len(scorecard_df)}")
print(f"  Green: {_n_green}  |  Amber: {_n_amber}  |  Red: {_n_red}")
print(f"{'='*60}")
