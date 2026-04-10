# ===========================================================================
# RETENTION & CHURN DATA: Account Status Classification (Conference Edition)
# ===========================================================================
# Builds retention_df with account health status:
#   Active, Declining, Dormant, Closed.
# Uses Date Closed, Stat Code/Desc, and monthly spend trajectory.
# Data only -- no charts.

_all_cols = rewards_df.columns.tolist()

# -----------------------------------------------------------------------
# 1. Discover monthly Spend columns and sort chronologically
# -----------------------------------------------------------------------
_MONTH_MAP = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
              'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}

def _spend_sort_key(col_name):
    label = col_name.replace(' Spend', '')
    try:
        return (2000 + int(label[3:])) * 100 + _MONTH_MAP.get(label[:3], 0)
    except (ValueError, IndexError):
        return 999999

_spend_cols = sorted(
    [c for c in _all_cols if c.endswith(' Spend')
     and not c.startswith('Total') and not c.startswith('last')],
    key=_spend_sort_key
)
_month_labels = [c.replace(' Spend', '') for c in _spend_cols]

if len(_spend_cols) == 0:
    print("    No monthly Spend columns found. Skipping retention data.")
    retention_df = pd.DataFrame()
else:
    acct_col = 'Acct Number' if 'Acct Number' in _all_cols else ' Acct Number'

    # -----------------------------------------------------------------------
    # 2. Build per-account retention dataset
    # -----------------------------------------------------------------------
    _keep_cols = [acct_col]

    # Optional fields
    _has_date_closed = 'Date Closed' in _all_cols
    _has_stat_code = 'Stat Code' in _all_cols
    _has_stat_desc = 'Stat Desc' in _all_cols
    _has_date_opened = 'Date Opened' in _all_cols
    _has_age = 'Account Holder Age' in _all_cols
    _has_avg_bal = 'Avg Bal' in _all_cols

    if _has_date_closed:
        _keep_cols.append('Date Closed')
    if _has_stat_code:
        _keep_cols.append('Stat Code')
    if _has_stat_desc:
        _keep_cols.append('Stat Desc')
    if _has_date_opened:
        _keep_cols.append('Date Opened')
    if _has_age:
        _keep_cols.append('Account Holder Age')
    if _has_avg_bal:
        _keep_cols.append('Avg Bal')

    retention_df = rewards_df[_keep_cols + _spend_cols].copy()
    retention_df.rename(columns={acct_col: 'acct_number'}, inplace=True)
    retention_df['acct_number'] = retention_df['acct_number'].astype(str).str.strip()

    # Convert spend columns to numeric
    for sc in _spend_cols:
        retention_df[sc] = pd.to_numeric(retention_df[sc], errors='coerce').fillna(0)

    # -----------------------------------------------------------------------
    # 3. Compute monthly spend trajectory
    # -----------------------------------------------------------------------
    _spend_matrix = retention_df[_spend_cols].values
    num_months = len(_spend_cols)

    # Last 3 months spend
    _last3 = min(3, num_months)
    retention_df['last_3mo_avg_spend'] = _spend_matrix[:, -_last3:].mean(axis=1)

    # Prior 3 months (months -6 to -3)
    if num_months >= 6:
        retention_df['prior_3mo_avg_spend'] = _spend_matrix[:, -6:-3].mean(axis=1)
    else:
        retention_df['prior_3mo_avg_spend'] = _spend_matrix[:, :max(1, num_months - _last3)].mean(axis=1)

    # Spend trend: simple slope over last 6 months (positive = growing)
    _trend_months = min(6, num_months)
    _trend_data = _spend_matrix[:, -_trend_months:]
    _x = np.arange(_trend_months)
    _x_mean = _x.mean()
    _x_var = ((_x - _x_mean) ** 2).sum()
    if _x_var > 0:
        _y_means = _trend_data.mean(axis=0)
        # Vectorized slope for all accounts
        _slopes = ((_trend_data - _trend_data.mean(axis=1, keepdims=True)) * (_x - _x_mean)).sum(axis=1) / _x_var
        retention_df['spend_slope'] = _slopes
    else:
        retention_df['spend_slope'] = 0.0

    # Count consecutive zero-spend months from end
    _zero_months = np.zeros(len(retention_df), dtype=int)
    for i in range(num_months - 1, -1, -1):
        _still_zero = _spend_matrix[:, i] == 0
        _zero_months = np.where(_still_zero & (_zero_months == (num_months - 1 - i)), _zero_months + 1, _zero_months)
    retention_df['consecutive_zero_months'] = _zero_months

    # -----------------------------------------------------------------------
    # 4. Parse Date Closed
    # -----------------------------------------------------------------------
    if _has_date_closed:
        retention_df['closed_date'] = pd.to_datetime(
            retention_df['Date Closed'], errors='coerce'
        )
        retention_df['is_closed'] = retention_df['closed_date'].notna()
    else:
        retention_df['is_closed'] = False
        retention_df['closed_date'] = pd.NaT

    # Tenure at close
    if _has_date_opened:
        retention_df['date_opened'] = pd.to_datetime(
            retention_df['Date Opened'], errors='coerce'
        )
        retention_df['tenure_months'] = (
            (retention_df['closed_date'].fillna(DATASET_END) - retention_df['date_opened'])
            .dt.days / 30.44
        ).clip(lower=0)
    else:
        retention_df['tenure_months'] = np.nan

    # -----------------------------------------------------------------------
    # 5. Classify account health status
    # -----------------------------------------------------------------------
    def _classify_health(row):
        if row['is_closed']:
            return 'Closed'
        if row['consecutive_zero_months'] >= 3:
            return 'Dormant'
        if row['consecutive_zero_months'] >= 1 and row['last_3mo_avg_spend'] < row['prior_3mo_avg_spend'] * 0.5:
            return 'Cooling'
        if row['spend_slope'] < -5 and row['prior_3mo_avg_spend'] > 0:
            return 'Declining'
        return 'Active'

    retention_df['health_status'] = retention_df.apply(_classify_health, axis=1)

    # -----------------------------------------------------------------------
    # 6. Merge engagement tier (if available)
    # -----------------------------------------------------------------------
    if 'acct_txn_counts' in dir() and len(acct_txn_counts) > 0:
        _eng_map = acct_txn_counts.set_index('account')['tier'].to_dict()
        retention_df['engagement_tier'] = retention_df['acct_number'].map(_eng_map).fillna('Unknown')
    else:
        retention_df['engagement_tier'] = 'Unknown'

    # Merge PFI tier (if available)
    if 'pfi_df' in dir() and isinstance(pfi_df, pd.DataFrame) and len(pfi_df) > 0:
        if 'acct_number' in pfi_df.columns and 'pfi_tier' in pfi_df.columns:
            _pfi_map = pfi_df.set_index('acct_number')['pfi_tier'].to_dict()
            retention_df['pfi_tier'] = retention_df['acct_number'].map(_pfi_map).fillna('Unknown')
        else:
            retention_df['pfi_tier'] = 'Unknown'
    else:
        retention_df['pfi_tier'] = 'Unknown'

    # Age band
    if _has_age:
        retention_df['age'] = pd.to_numeric(retention_df['Account Holder Age'], errors='coerce')
        retention_df['age_band'] = pd.cut(
            retention_df['age'],
            bins=[0, 25, 35, 45, 55, 65, 200],
            labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+'],
            right=True
        ).astype(str).replace('nan', 'Unknown')
    else:
        retention_df['age_band'] = 'Unknown'

    # Pre-close monthly spend (for attrition cost)
    retention_df['pre_close_monthly_spend'] = retention_df['prior_3mo_avg_spend']

    # -----------------------------------------------------------------------
    # 7. Retention palette & order
    # -----------------------------------------------------------------------
    HEALTH_PALETTE = {
        'Active':    GEN_COLORS['success'],
        'Declining': GEN_COLORS['warning'],
        'Cooling':   '#F4A261',
        'Dormant':   GEN_COLORS['muted'],
        'Closed':    GEN_COLORS['accent'],
    }
    HEALTH_ORDER = ['Active', 'Declining', 'Cooling', 'Dormant', 'Closed']

    # -----------------------------------------------------------------------
    # 8. Summary
    # -----------------------------------------------------------------------
    _total = len(retention_df)
    print("Retention data built.")
    print(f"  Total accounts: {_total:,}")
    print(f"  Monthly spend columns: {num_months} ({_month_labels[0]} - {_month_labels[-1]})")
    print()
    for _status in HEALTH_ORDER:
        _count = (retention_df['health_status'] == _status).sum()
        _pct = _count / _total * 100 if _total > 0 else 0
        _avg_spend = retention_df.loc[retention_df['health_status'] == _status, 'last_3mo_avg_spend'].mean()
        print(f"  {_status:>10s}: {_count:>6,} ({_pct:>5.1f}%)  avg last-3mo spend: ${_avg_spend:,.0f}")

    if _has_date_closed:
        _closed_count = retention_df['is_closed'].sum()
        print(f"\n  Accounts with Date Closed: {_closed_count:,}")
        if _closed_count > 0 and _has_date_opened:
            _avg_tenure = retention_df.loc[retention_df['is_closed'], 'tenure_months'].mean()
            print(f"  Avg tenure at close: {_avg_tenure:.0f} months")
