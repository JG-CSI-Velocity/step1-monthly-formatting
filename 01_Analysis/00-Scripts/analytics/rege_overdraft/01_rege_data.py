# ===========================================================================
# REG E / OVERDRAFT DATA: Build Analysis DataFrames from ODDD Snapshots
# ===========================================================================
# Auto-discover Reg E and OD Limit columns, build long-format time series,
# classify opt-in status, track status changes. All downstream cells depend
# on this.

import re
from collections import OrderedDict

# ---------------------------------------------------------------------------
# 1. Auto-discover Reg E and OD Limit columns
# ---------------------------------------------------------------------------
_rege_code_pattern = re.compile(r'^([A-Z][a-z]{2}\d{2})\s+Reg\s+E\s+Code$')
_rege_desc_pattern = re.compile(r'^([A-Z][a-z]{2}\d{2})\s+Reg\s+E\s+Desc$')
_od_limit_pattern = re.compile(r'^([A-Z][a-z]{2}\d{2})\s+OD\s+Limit$')

# Maps: month_key -> column_name
rege_code_cols = OrderedDict()
rege_desc_cols = OrderedDict()
od_limit_cols = OrderedDict()

for col in rewards_df.columns:
    m = _rege_code_pattern.match(col)
    if m:
        rege_code_cols[m.group(1)] = col
        continue
    m = _rege_desc_pattern.match(col)
    if m:
        rege_desc_cols[m.group(1)] = col
        continue
    m = _od_limit_pattern.match(col)
    if m:
        od_limit_cols[m.group(1)] = col

# Sort months chronologically (Mon-YY format)
_month_order = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12,
}

def _month_sort_key(key):
    """Convert 'Sep24' to (2024, 9) for chronological sorting."""
    mon_str = key[:3]
    yr_str = key[3:]
    yr = int(yr_str) + 2000
    return (yr, _month_order.get(mon_str, 0))

_sorted_months = sorted(
    set(list(rege_code_cols.keys()) + list(od_limit_cols.keys())),
    key=_month_sort_key
)

REGE_MONTHS = _sorted_months
REGE_MONTH_LABELS = [f"{m[:3]} '{m[3:]}" for m in _sorted_months]

print(f"    Discovered {len(rege_code_cols)} Reg E Code columns")
print(f"    Discovered {len(rege_desc_cols)} Reg E Desc columns")
print(f"    Discovered {len(od_limit_cols)} OD Limit columns")
print(f"    Month span: {REGE_MONTHS[0] if REGE_MONTHS else 'N/A'} to "
      f"{REGE_MONTHS[-1] if REGE_MONTHS else 'N/A'}")

# ---------------------------------------------------------------------------
# 2. Build long-format monthly Reg E time series
# ---------------------------------------------------------------------------
_monthly_records = []

for month_key in REGE_MONTHS:
    code_col = rege_code_cols.get(month_key)
    desc_col = rege_desc_cols.get(month_key)
    od_col = od_limit_cols.get(month_key)

    for idx, row in rewards_df.iterrows():
        record = {
            'account_number': row.get('Acct Number', idx),
            'month_key': month_key,
            'rege_code': row[code_col] if code_col and code_col in rewards_df.columns else None,
            'rege_desc': row[desc_col] if desc_col and desc_col in rewards_df.columns else None,
            'od_limit': pd.to_numeric(
                row[od_col], errors='coerce'
            ) if od_col and od_col in rewards_df.columns else np.nan,
        }
        _monthly_records.append(record)

monthly_rege = pd.DataFrame(_monthly_records)
monthly_rege['month_sort'] = monthly_rege['month_key'].apply(
    lambda k: _month_sort_key(k)
)
monthly_rege = monthly_rege.sort_values(['account_number', 'month_sort']).reset_index(drop=True)

print(f"    monthly_rege built: {len(monthly_rege):,} rows "
      f"({monthly_rege['account_number'].nunique():,} accounts x "
      f"{monthly_rege['month_key'].nunique()} months)")

# ---------------------------------------------------------------------------
# 3. Classify Reg E status using discovered codes
# ---------------------------------------------------------------------------
# Discover distinct code values and classify them
_all_codes = monthly_rege['rege_code'].dropna().unique()
_all_descs = monthly_rege['rege_desc'].dropna().str.lower().unique()

# Heuristic classification of Reg E codes using descriptions
# Opt-in keywords: opted in, opt in, consent, authorized, enrolled, yes
# Opt-out keywords: opted out, opt out, declined, not authorized, no
_optin_keywords = re.compile(
    r'opt[\-\s]*in|consent|authorized|enrolled|(?:^|\s)yes(?:\s|$)', re.IGNORECASE
)
_optout_keywords = re.compile(
    r'opt[\-\s]*out|decline|not\s+authorized|(?:^|\s)no(?:\s|$)', re.IGNORECASE
)
_na_keywords = re.compile(
    r'not\s+applicable|n/?a|none|exempt', re.IGNORECASE
)

# Build code -> status mapping from descriptions
_code_status_map = {}
_code_to_desc = (
    monthly_rege.dropna(subset=['rege_code', 'rege_desc'])
    .drop_duplicates(subset=['rege_code'])
    .set_index('rege_code')['rege_desc']
    .to_dict()
)

for code, desc in _code_to_desc.items():
    desc_str = str(desc)
    if _optin_keywords.search(desc_str):
        _code_status_map[code] = 'Opted-In'
    elif _optout_keywords.search(desc_str):
        _code_status_map[code] = 'Opted-Out'
    elif _na_keywords.search(desc_str):
        _code_status_map[code] = 'Not Applicable'
    else:
        _code_status_map[code] = 'Unknown'

# If no description-based classification worked, try code values directly
if not _code_status_map:
    for code in _all_codes:
        code_str = str(code).strip().upper()
        if code_str in ('Y', '1', 'YES', 'TRUE', 'OPT-IN', 'OPTIN'):
            _code_status_map[code] = 'Opted-In'
        elif code_str in ('N', '0', 'NO', 'FALSE', 'OPT-OUT', 'OPTOUT'):
            _code_status_map[code] = 'Opted-Out'
        elif code_str in ('', 'NA', 'N/A', 'NONE'):
            _code_status_map[code] = 'Not Applicable'
        else:
            _code_status_map[code] = 'Unknown'

REGE_STATUS_MAP = _code_status_map
print(f"    Reg E code -> status mapping:")
for code, status in sorted(REGE_STATUS_MAP.items(), key=lambda x: str(x[0])):
    desc = _code_to_desc.get(code, '(no desc)')
    print(f"      {str(code):>10s} -> {status:<16s}  [{desc}]")

monthly_rege['rege_status'] = monthly_rege['rege_code'].map(REGE_STATUS_MAP).fillna('Unknown')

# ---------------------------------------------------------------------------
# 4. Per-account: earliest status, latest status, status change tracking
# ---------------------------------------------------------------------------
_earliest_month = REGE_MONTHS[0] if REGE_MONTHS else None
_latest_month = REGE_MONTHS[-1] if REGE_MONTHS else None

_first = monthly_rege[monthly_rege['month_key'] == _earliest_month][
    ['account_number', 'rege_code', 'rege_desc', 'rege_status', 'od_limit']
].rename(columns={
    'rege_code': 'first_rege_code',
    'rege_desc': 'first_rege_desc',
    'rege_status': 'first_status',
    'od_limit': 'first_od_limit',
})

_last = monthly_rege[monthly_rege['month_key'] == _latest_month][
    ['account_number', 'rege_code', 'rege_desc', 'rege_status', 'od_limit']
].rename(columns={
    'rege_code': 'latest_rege_code',
    'rege_desc': 'latest_rege_desc',
    'rege_status': 'current_status',
    'od_limit': 'current_od_limit',
})

rege_df = _first.merge(_last, on='account_number', how='outer')

# Track status changes
rege_df['status_changed'] = rege_df['first_status'] != rege_df['current_status']
rege_df['change_direction'] = 'No Change'
rege_df.loc[
    (rege_df['first_status'] != 'Opted-In') & (rege_df['current_status'] == 'Opted-In'),
    'change_direction'
] = 'Newly Opted-In'
rege_df.loc[
    (rege_df['first_status'] == 'Opted-In') & (rege_df['current_status'] != 'Opted-In'),
    'change_direction'
] = 'Newly Opted-Out'
rege_df.loc[
    (rege_df['first_status'] == 'Opted-Out') & (rege_df['current_status'] == 'Opted-In'),
    'change_direction'
] = 'Newly Opted-In'

# Merge demographic columns from rewards_df
_demo_cols = ['Acct Number', 'Account Holder Age', 'Avg Bal', 'Curr Bal',
              'Prod Code', 'Prod Desc', 'Business?', 'Branch']
_available_demo = [c for c in _demo_cols if c in rewards_df.columns]

if 'Acct Number' in _available_demo:
    _demo = rewards_df[_available_demo].copy()
    _demo = _demo.rename(columns={'Acct Number': 'account_number'})
    rege_df = rege_df.merge(_demo, on='account_number', how='left')

# Coerce numerics
for _col in ['Account Holder Age', 'Avg Bal', 'Curr Bal', 'current_od_limit', 'first_od_limit']:
    if _col in rege_df.columns:
        rege_df[_col] = pd.to_numeric(rege_df[_col], errors='coerce')

# Age bands
if 'Account Holder Age' in rege_df.columns:
    rege_df['age_band'] = pd.cut(
        rege_df['Account Holder Age'],
        bins=[0, 25, 35, 45, 55, 65, 200],
        labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+'],
        right=True
    ).astype(str).replace('nan', 'Unknown')

# Balance bands
if 'Avg Bal' in rege_df.columns:
    rege_df['balance_band'] = pd.cut(
        rege_df['Avg Bal'],
        bins=[-999999, 0, 500, 2000, 5000, 10000, 999999999],
        labels=['Negative', '$0-500', '$500-2K', '$2K-5K', '$5K-10K', '$10K+'],
        right=True
    ).astype(str).replace('nan', 'Unknown')

# Merge engagement tier if available
try:
    if acct_txn_counts is not None and 'engage_tier' in acct_txn_counts.columns:
        _engage = acct_txn_counts[['Acct Number', 'engage_tier']].copy()
        _engage = _engage.rename(columns={'Acct Number': 'account_number'})
        rege_df = rege_df.merge(_engage, on='account_number', how='left')
        rege_df['engage_tier'] = rege_df['engage_tier'].fillna('Unknown')
except NameError:
    rege_df['engage_tier'] = 'Unknown'

# ---------------------------------------------------------------------------
# 5. Build OD Limit time series
# ---------------------------------------------------------------------------
_od_records = []
for month_key in REGE_MONTHS:
    od_col = od_limit_cols.get(month_key)
    if od_col and od_col in rewards_df.columns:
        _od_month = pd.DataFrame({
            'account_number': rewards_df.get('Acct Number', rewards_df.index),
            'month_key': month_key,
            'od_limit': pd.to_numeric(rewards_df[od_col], errors='coerce'),
        })
        _od_records.append(_od_month)

if _od_records:
    od_df = pd.concat(_od_records, ignore_index=True)
    od_df['month_sort'] = od_df['month_key'].apply(_month_sort_key)
    od_df = od_df.sort_values(['account_number', 'month_sort']).reset_index(drop=True)
else:
    od_df = pd.DataFrame(columns=['account_number', 'month_key', 'od_limit', 'month_sort'])

# ---------------------------------------------------------------------------
# 6. Palettes and constants for downstream cells
# ---------------------------------------------------------------------------
REGE_STATUS_PALETTE = {
    'Opted-In':       GEN_COLORS['success'],
    'Opted-Out':      GEN_COLORS['accent'],
    'Not Applicable': GEN_COLORS['muted'],
    'Unknown':        GEN_COLORS['grid'],
}
REGE_STATUS_ORDER = ['Opted-In', 'Opted-Out', 'Not Applicable', 'Unknown']

CHANGE_PALETTE = {
    'No Change':       GEN_COLORS['info'],
    'Newly Opted-In':  GEN_COLORS['success'],
    'Newly Opted-Out': GEN_COLORS['accent'],
}

OD_LIMIT_BANDS = ['$0', '$1-100', '$100-500', '$500-1K', '$1K+']
OD_LIMIT_PALETTE = [
    GEN_COLORS['muted'], '#A8DADC', '#457B9D', '#FF9F1C', GEN_COLORS['accent']
]

# ---------------------------------------------------------------------------
# 7. Summary printout
# ---------------------------------------------------------------------------
_total = len(rege_df)
_opted_in = len(rege_df[rege_df['current_status'] == 'Opted-In'])
_opted_out = len(rege_df[rege_df['current_status'] == 'Opted-Out'])
_changed = rege_df['status_changed'].sum()
_avg_od = rege_df.loc[rege_df['current_status'] == 'Opted-In', 'current_od_limit'].mean()

print(f"\n    Reg E / Overdraft data built: {_total:,} accounts")
print(f"    Months covered: {len(REGE_MONTHS)} ({REGE_MONTHS[0]} to {REGE_MONTHS[-1]})")
print(f"    Current opt-in rate: {(_opted_in / _total * 100) if _total > 0 else 0:.1f}%"
      f"  ({_opted_in:,} accounts)")
print(f"    Current opt-out: {_opted_out:,} accounts")
print(f"    Avg OD Limit (opted-in): ${_avg_od:,.0f}" if not pd.isna(_avg_od) else
      "    Avg OD Limit: N/A")
print(f"    Status changed over period: {_changed:,} accounts")
print(f"    monthly_rege rows: {len(monthly_rege):,}")
print(f"    od_df rows: {len(od_df):,}")
