# ===========================================================================
# ATTRITION DATA: Build Risk Tiers from ODDD Velocity Metrics
# ===========================================================================
# Compute spend/swipe velocity ratios, classify risk tiers, build monthly
# time series. All downstream attrition cells depend on this.

# ---------------------------------------------------------------------------
# Extract relevant columns from rewards_df
# ---------------------------------------------------------------------------
_attrition_cols = {
    'Acct Number': 'account_number',
    'last 3-mon spend': 'last_3mo_spend',
    'last 3-mon swipes': 'last_3mo_swipes',
    'last 12-mon spend': 'last_12mo_spend',
    'last 12-mon swipes': 'last_12mo_swipes',
    'MonthlySpend3': 'monthly_spend_3',
    'MonthlySpend12': 'monthly_spend_12',
    'MonthlySwipes3': 'monthly_swipes_3',
    'MonthlySwipes12': 'monthly_swipes_12',
    'Stat Code': 'stat_code',
    'Stat Desc': 'stat_desc',
    'Avg Bal': 'avg_bal',
    'Curr Bal': 'curr_bal',
    'Account Holder Age': 'holder_age',
    'Prod Code': 'prod_code',
    'Prod Desc': 'prod_desc',
}

available_cols = {k: v for k, v in _attrition_cols.items() if k in rewards_df.columns}
missing_cols = [k for k in _attrition_cols if k not in rewards_df.columns]

if missing_cols:
    print(f"    NOTE: {len(missing_cols)} columns not found in rewards_df:")
    for mc in missing_cols:
        print(f"      - {mc}")

attrition_df = rewards_df[list(available_cols.keys())].copy()
attrition_df.columns = [available_cols[c] for c in attrition_df.columns]

# ---------------------------------------------------------------------------
# Coerce numeric columns
# ---------------------------------------------------------------------------
_numeric_cols = [
    'last_3mo_spend', 'last_3mo_swipes', 'last_12mo_spend', 'last_12mo_swipes',
    'monthly_spend_3', 'monthly_spend_12', 'monthly_swipes_3', 'monthly_swipes_12',
    'avg_bal', 'curr_bal', 'holder_age',
]
for _col in _numeric_cols:
    if _col in attrition_df.columns:
        attrition_df[_col] = pd.to_numeric(attrition_df[_col], errors='coerce').fillna(0)

# ---------------------------------------------------------------------------
# Velocity ratios (annualized: multiply 3-month ratio by 4)
# >1 = growing, <1 = declining, 0 = no baseline
# ---------------------------------------------------------------------------
def _safe_velocity(recent, annual):
    """Compute annualized velocity ratio, handling division by zero."""
    if annual == 0:
        return 0.0 if recent == 0 else 2.0  # new activity = strong signal
    return (recent / annual) * 4

if 'last_3mo_spend' in attrition_df.columns and 'last_12mo_spend' in attrition_df.columns:
    attrition_df['spend_velocity'] = attrition_df.apply(
        lambda r: _safe_velocity(r['last_3mo_spend'], r['last_12mo_spend']), axis=1
    )
else:
    attrition_df['spend_velocity'] = 1.0

if 'last_3mo_swipes' in attrition_df.columns and 'last_12mo_swipes' in attrition_df.columns:
    attrition_df['swipe_velocity'] = attrition_df.apply(
        lambda r: _safe_velocity(r['last_3mo_swipes'], r['last_12mo_swipes']), axis=1
    )
else:
    attrition_df['swipe_velocity'] = 1.0

# ---------------------------------------------------------------------------
# Risk tier classification
# ---------------------------------------------------------------------------
# Inspect actual stat codes for closed detection
_stat_codes = set()
if 'stat_code' in attrition_df.columns:
    _stat_codes = set(attrition_df['stat_code'].dropna().unique())
if 'stat_desc' in attrition_df.columns:
    _stat_descs = attrition_df['stat_desc'].dropna().str.lower().unique()
else:
    _stat_descs = []

# Detect closed status keywords
CLOSED_CODES = set()
if 'stat_desc' in attrition_df.columns:
    _closed_mask = attrition_df['stat_desc'].fillna('').str.lower().str.contains(
        'closed|revoked|cancelled|charged off|frozen|deceased|bankrupt', regex=True
    )
else:
    _closed_mask = pd.Series(False, index=attrition_df.index)

def _classify_risk(row, is_closed):
    """Classify account into attrition risk tier."""
    if is_closed:
        return 'Closed'

    sv = row['spend_velocity']
    wv = row['swipe_velocity']

    # Zero recent activity = dormant
    has_3mo_spend = row.get('last_3mo_spend', 0) > 0
    has_3mo_swipes = row.get('last_3mo_swipes', 0) > 0

    if not has_3mo_spend and not has_3mo_swipes:
        return 'Dormant'

    if sv < 0.2 and wv < 0.2:
        return 'Dormant'

    if sv < 0.8 or wv < 0.8:
        return 'Declining'

    if sv > 1.1 and wv > 1.1:
        return 'Growing'

    return 'Stable'

attrition_df['risk_tier'] = [
    _classify_risk(row, closed)
    for row, closed in zip(
        attrition_df.to_dict('records'),
        _closed_mask
    )
]

RISK_ORDER = ['Growing', 'Stable', 'Declining', 'Dormant', 'Closed']
RISK_PALETTE = {
    'Growing':   GEN_COLORS['success'],
    'Stable':    GEN_COLORS['info'],
    'Declining': GEN_COLORS['warning'],
    'Dormant':   GEN_COLORS['muted'],
    'Closed':    GEN_COLORS['accent'],
}

# ---------------------------------------------------------------------------
# Monthly spend time series (Sep24 Spend .. Jan26 Spend)
# ---------------------------------------------------------------------------
_month_spend_cols = [c for c in rewards_df.columns if c.endswith(' Spend') and len(c) <= 12]
_month_spend_cols = sorted(_month_spend_cols, key=lambda c: c)  # alphabetical as fallback

if _month_spend_cols:
    # Build long-format time series
    _ts_id = rewards_df[['Acct Number']].copy()
    _ts_id.columns = ['account_number']
    for mc in _month_spend_cols:
        _ts_id[mc] = pd.to_numeric(rewards_df[mc], errors='coerce').fillna(0)

    monthly_spend_ts = _ts_id.melt(
        id_vars='account_number',
        value_vars=_month_spend_cols,
        var_name='month_label',
        value_name='spend',
    )
    monthly_spend_ts['month_label'] = monthly_spend_ts['month_label'].str.replace(' Spend', '')

    # Merge risk tier
    _tier_map = attrition_df[['account_number', 'risk_tier']].drop_duplicates()
    monthly_spend_ts = monthly_spend_ts.merge(_tier_map, on='account_number', how='left')

    print(f"    Monthly spend time series: {len(_month_spend_cols)} months, "
          f"{monthly_spend_ts['account_number'].nunique():,} accounts")
else:
    monthly_spend_ts = pd.DataFrame()
    print("    NOTE: No monthly spend columns found for time series")

# ---------------------------------------------------------------------------
# Risk tier summary
# ---------------------------------------------------------------------------
_total_accts = len(attrition_df)
tier_summary = []
for tier in RISK_ORDER:
    tier_data = attrition_df[attrition_df['risk_tier'] == tier]
    _count = len(tier_data)
    tier_summary.append({
        'Risk Tier': tier,
        'Accounts': _count,
        'Pct': (_count / _total_accts * 100) if _total_accts > 0 else 0,
        'Avg Spend Velocity': tier_data['spend_velocity'].mean() if _count > 0 else 0,
        'Avg Swipe Velocity': tier_data['swipe_velocity'].mean() if _count > 0 else 0,
        'Avg Balance': tier_data['avg_bal'].mean() if _count > 0 and 'avg_bal' in tier_data.columns else 0,
    })

tier_summary_df = pd.DataFrame(tier_summary)

# Styled summary table
styled = (
    tier_summary_df.style
    .hide(axis='index')
    .format({
        'Accounts': '{:,.0f}',
        'Pct': '{:.1f}%',
        'Avg Spend Velocity': '{:.2f}x',
        'Avg Swipe Velocity': '{:.2f}x',
        'Avg Balance': '${:,.0f}',
    })
    .set_properties(**{
        'font-size': '15px',
        'font-weight': 'bold',
        'text-align': 'center',
        'border': '1px solid #E9ECEF',
        'padding': '10px 14px',
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', GEN_COLORS['primary']),
            ('color', 'white'),
            ('font-size', '16px'),
            ('font-weight', 'bold'),
            ('text-align', 'center'),
            ('padding', '10px 14px'),
        ]},
        {'selector': 'caption', 'props': [
            ('font-size', '22px'),
            ('font-weight', 'bold'),
            ('color', GEN_COLORS['dark_text']),
            ('text-align', 'left'),
            ('padding-bottom', '12px'),
        ]},
    ])
    .set_caption("Attrition Risk Tier Summary")
    .bar(subset=['Accounts'], color=GEN_COLORS['info'], vmin=0)
)

display(styled)

print(f"\n    Attrition data built: {_total_accts:,} accounts classified")
print(f"    Velocity > 1.0 = growing, < 1.0 = declining, 0 = no baseline")
for _, row in tier_summary_df.iterrows():
    print(f"      {row['Risk Tier']:>10s}: {row['Accounts']:>6,} accounts ({row['Pct']:.1f}%)")
