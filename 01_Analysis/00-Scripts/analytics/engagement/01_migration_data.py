# ===========================================================================
# ENGAGEMENT MIGRATION DATA: Monthly Tier Classification (Conference Edition)
# ===========================================================================
# Computes engagement tier per account per month from MmmYY Spend + Swipes.
# Tracks tier-to-tier movement across consecutive months.
# Builds: migration_df, monthly_transitions, migration_summary.
# Data only -- no charts.

_all_cols = rewards_df.columns.tolist()

# -----------------------------------------------------------------------
# 1. Discover monthly columns
# -----------------------------------------------------------------------
_MONTH_MAP = {'Jan':1,'Feb':2,'Mar':3,'Apr':4,'May':5,'Jun':6,
              'Jul':7,'Aug':8,'Sep':9,'Oct':10,'Nov':11,'Dec':12}

def _mig_sort_key(col_name):
    label = col_name.replace(' Spend', '').replace(' Swipes', '')
    try:
        return (2000 + int(label[3:])) * 100 + _MONTH_MAP.get(label[:3], 0)
    except (ValueError, IndexError):
        return 999999

_spend_cols = sorted(
    [c for c in _all_cols if c.endswith(' Spend')
     and not c.startswith('Total') and not c.startswith('last')],
    key=_mig_sort_key
)
_swipe_cols = sorted(
    [c for c in _all_cols if c.endswith(' Swipes')
     and not c.startswith('Total') and not c.startswith('last')],
    key=_mig_sort_key
)
_month_labels = [c.replace(' Spend', '') for c in _spend_cols]

if len(_spend_cols) < 3:
    print("    Need at least 3 months of data for migration analysis. Skipping.")
    migration_summary = pd.DataFrame()
    monthly_transitions = pd.DataFrame()
else:
    acct_col = 'Acct Number' if 'Acct Number' in _all_cols else ' Acct Number'

    # -----------------------------------------------------------------------
    # 2. Build monthly activity matrix
    # -----------------------------------------------------------------------
    _acct_ids = rewards_df[acct_col].astype(str).str.strip()

    # Convert all spend columns to numeric at once
    _spend_data = rewards_df[_spend_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    # Also get swipe data if columns match
    _swipe_data = None
    if len(_swipe_cols) == len(_spend_cols):
        _swipe_data = rewards_df[_swipe_cols].apply(pd.to_numeric, errors='coerce').fillna(0)

    # -----------------------------------------------------------------------
    # 3. Classify engagement tier per month
    # -----------------------------------------------------------------------
    # Use combined spend + swipes as activity score (if both available)
    # Tier thresholds: consistent across all months for comparability
    # Power: top 5%, Heavy: 5-20%, Moderate: 20-60%, Light: 60-90%, Dormant: bottom 10%

    # Compute overall activity score (avg across all months) for threshold setting
    _overall_activity = _spend_data.mean(axis=1)
    if _swipe_data is not None:
        _overall_swipes = _swipe_data.mean(axis=1)
        _overall_activity = _overall_activity + _overall_swipes * 10  # weight swipes

    # Set fixed thresholds from overall distribution
    _thresholds = {
        'p5': np.percentile(_overall_activity[_overall_activity > 0], 95),
        'p20': np.percentile(_overall_activity[_overall_activity > 0], 80),
        'p60': np.percentile(_overall_activity[_overall_activity > 0], 40),
        'p90': np.percentile(_overall_activity[_overall_activity > 0], 10),
    }

    def _classify_tier(activity_score):
        if activity_score <= 0:
            return 'Dormant'
        if activity_score >= _thresholds['p5']:
            return 'Power'
        if activity_score >= _thresholds['p20']:
            return 'Heavy'
        if activity_score >= _thresholds['p60']:
            return 'Moderate'
        if activity_score >= _thresholds['p90']:
            return 'Light'
        return 'Dormant'

    # Compute tier per month
    _monthly_tiers = {}
    for i, month_label in enumerate(_month_labels):
        _month_activity = _spend_data.iloc[:, i].values
        if _swipe_data is not None:
            _month_activity = _month_activity + _swipe_data.iloc[:, i].values * 10

        _tiers = pd.Series(_month_activity).apply(_classify_tier)
        _monthly_tiers[month_label] = _tiers.values

    _tier_df = pd.DataFrame(_monthly_tiers, index=_acct_ids)
    _tier_df.index.name = 'acct_number'

    # -----------------------------------------------------------------------
    # 4. Compute month-over-month transitions
    # -----------------------------------------------------------------------
    _transitions = []
    for i in range(len(_month_labels) - 1):
        _from_month = _month_labels[i]
        _to_month = _month_labels[i + 1]
        _from_tiers = _tier_df[_from_month]
        _to_tiers = _tier_df[_to_month]

        _xtab = pd.crosstab(_from_tiers, _to_tiers)

        # Classify each account transition
        _tier_rank = {'Power': 0, 'Heavy': 1, 'Moderate': 2, 'Light': 3, 'Dormant': 4}
        _from_rank = _from_tiers.map(_tier_rank)
        _to_rank = _to_tiers.map(_tier_rank)

        _upgraded = (_to_rank < _from_rank).sum()
        _downgraded = (_to_rank > _from_rank).sum()
        _stable = (_to_rank == _from_rank).sum()
        _total = len(_from_tiers)

        _transitions.append({
            'from_month': _from_month,
            'to_month': _to_month,
            'upgraded': _upgraded,
            'downgraded': _downgraded,
            'stable': _stable,
            'total': _total,
            'net_migration': _upgraded - _downgraded,
            'upgrade_rate': _upgraded / _total * 100 if _total > 0 else 0,
            'downgrade_rate': _downgraded / _total * 100 if _total > 0 else 0,
            'stability_rate': _stable / _total * 100 if _total > 0 else 0,
        })

    monthly_transitions = pd.DataFrame(_transitions)

    # -----------------------------------------------------------------------
    # 5. Overall migration summary (first month -> last month)
    # -----------------------------------------------------------------------
    _first_month = _month_labels[0]
    _last_month = _month_labels[-1]
    _first_tiers = _tier_df[_first_month]
    _last_tiers = _tier_df[_last_month]

    _tier_rank = {'Power': 0, 'Heavy': 1, 'Moderate': 2, 'Light': 3, 'Dormant': 4}
    _first_rank = _first_tiers.map(_tier_rank)
    _last_rank = _last_tiers.map(_tier_rank)

    _total_upgraded = (_last_rank < _first_rank).sum()
    _total_downgraded = (_last_rank > _first_rank).sum()
    _total_stable = (_last_rank == _first_rank).sum()

    # Migration matrix (first -> last month)
    migration_matrix = pd.crosstab(_first_tiers, _last_tiers)
    _order = [t for t in ENGAGE_ORDER if t in migration_matrix.index or t in migration_matrix.columns]
    migration_matrix = migration_matrix.reindex(index=_order, columns=_order, fill_value=0)

    # Per-tier summary
    _rows = []
    for _tier in ENGAGE_ORDER:
        _start = (_first_tiers == _tier).sum()
        _end = (_last_tiers == _tier).sum()
        _net = _end - _start
        _rows.append({
            'tier': _tier,
            'start_count': _start,
            'end_count': _end,
            'net_change': _net,
            'net_pct': _net / _start * 100 if _start > 0 else 0,
        })
    migration_summary = pd.DataFrame(_rows)

    # Store tier_df for downstream use
    migration_tier_df = _tier_df

    # -----------------------------------------------------------------------
    # 6. Summary print
    # -----------------------------------------------------------------------
    _total = len(_tier_df)
    print("Engagement migration data built.")
    print(f"  Accounts: {_total:,}")
    print(f"  Period: {_first_month} -> {_last_month} ({len(_month_labels)} months)")
    print(f"\n  Overall migration ({_first_month} -> {_last_month}):")
    print(f"    Upgraded:   {_total_upgraded:>6,} ({_total_upgraded / _total * 100:.1f}%)")
    print(f"    Stable:     {_total_stable:>6,} ({_total_stable / _total * 100:.1f}%)")
    print(f"    Downgraded: {_total_downgraded:>6,} ({_total_downgraded / _total * 100:.1f}%)")
    print(f"    Net flow:   {_total_upgraded - _total_downgraded:+,}")

    print(f"\n  Tier changes ({_first_month} -> {_last_month}):")
    for _, row in migration_summary.iterrows():
        _arrow = '+' if row['net_change'] > 0 else ''
        print(f"    {row['tier']:>8s}: {row['start_count']:>6,} -> {row['end_count']:>6,} "
              f"({_arrow}{row['net_change']:,}, {row['net_pct']:+.1f}%)")
