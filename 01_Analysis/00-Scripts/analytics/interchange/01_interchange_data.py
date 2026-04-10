# ===========================================================================
# INTERCHANGE ANALYSIS -- DATA PREPARATION
# ===========================================================================
# Build interchange_df from rewards_df PIN/SIG columns.
# Auto-discovers monthly columns so this scales with future data.

import re

# -----------------------------------------------------------------------
# 1. Auto-discover monthly PIN / SIG columns via pattern matching
# -----------------------------------------------------------------------
all_cols = rewards_df.columns.tolist()

pin_dollar_cols = sorted([c for c in all_cols if re.match(r'[A-Z][a-z]{2}\d{2} PIN \$', c)])
sig_dollar_cols = sorted([c for c in all_cols if re.match(r'[A-Z][a-z]{2}\d{2} Sig \$', c)])
pin_count_cols  = sorted([c for c in all_cols if re.match(r'[A-Z][a-z]{2}\d{2} PIN #', c)])
sig_count_cols  = sorted([c for c in all_cols if re.match(r'[A-Z][a-z]{2}\d{2} Sig #', c)])

print(f"Discovered monthly columns:")
print(f"  PIN $ columns: {len(pin_dollar_cols)}")
print(f"  SIG $ columns: {len(sig_dollar_cols)}")
print(f"  PIN # columns: {len(pin_count_cols)}")
print(f"  SIG # columns: {len(sig_count_cols)}")

# Month label extraction helper
MONTH_MAP = {
    'Jan': 1, 'Feb': 2, 'Mar': 3, 'Apr': 4, 'May': 5, 'Jun': 6,
    'Jul': 7, 'Aug': 8, 'Sep': 9, 'Oct': 10, 'Nov': 11, 'Dec': 12
}

def _parse_month_label(col_name):
    """Extract (year, month_num, label) from 'Sep24 PIN $' style column."""
    match = re.match(r'([A-Z][a-z]{2})(\d{2})', col_name)
    if not match:
        return None
    mon_str, yr_str = match.group(1), match.group(2)
    year = 2000 + int(yr_str)
    month_num = MONTH_MAP.get(mon_str, 0)
    label = f"{mon_str}{yr_str}"
    return year, month_num, label

# Build ordered month labels from PIN $ columns (canonical order)
month_info = []
for col in pin_dollar_cols:
    parsed = _parse_month_label(col)
    if parsed:
        month_info.append(parsed)
month_info.sort(key=lambda x: (x[0], x[1]))
MONTH_LABELS = [m[2] for m in month_info]
print(f"  Month order: {MONTH_LABELS}")

# -----------------------------------------------------------------------
# 2. Pivot to long format: one row per account per month
# -----------------------------------------------------------------------
acct_col = 'Acct Number' if 'Acct Number' in all_cols else ' Acct Number'

long_rows = []
for label in MONTH_LABELS:
    pin_d_col = f"{label} PIN $"
    sig_d_col = f"{label} Sig $"
    pin_c_col = f"{label} PIN #"
    sig_c_col = f"{label} Sig #"

    chunk = rewards_df[[acct_col]].copy()
    chunk.columns = ['acct_number']
    chunk['month'] = label

    chunk['pin_dollars'] = pd.to_numeric(
        rewards_df[pin_d_col], errors='coerce').fillna(0) if pin_d_col in all_cols else 0
    chunk['sig_dollars'] = pd.to_numeric(
        rewards_df[sig_d_col], errors='coerce').fillna(0) if sig_d_col in all_cols else 0
    chunk['pin_count'] = pd.to_numeric(
        rewards_df[pin_c_col], errors='coerce').fillna(0) if pin_c_col in all_cols else 0
    chunk['sig_count'] = pd.to_numeric(
        rewards_df[sig_c_col], errors='coerce').fillna(0) if sig_c_col in all_cols else 0

    long_rows.append(chunk)

monthly_long_df = pd.concat(long_rows, ignore_index=True)
print(f"\nLong-format rows: {len(monthly_long_df):,}")

# -----------------------------------------------------------------------
# 3. Per-account totals
# -----------------------------------------------------------------------
acct_totals = monthly_long_df.groupby('acct_number').agg(
    total_pin_dollars=('pin_dollars', 'sum'),
    total_sig_dollars=('sig_dollars', 'sum'),
    total_pin_count=('pin_count', 'sum'),
    total_sig_count=('sig_count', 'sum'),
).reset_index()

# -----------------------------------------------------------------------
# 4. SIG ratio
# -----------------------------------------------------------------------
total_spend = acct_totals['total_pin_dollars'] + acct_totals['total_sig_dollars']
acct_totals['sig_ratio'] = np.where(
    total_spend > 0,
    acct_totals['total_sig_dollars'] / total_spend,
    np.nan
)

# -----------------------------------------------------------------------
# 5. Estimate interchange revenue (Durbin-exempt CU rates)
# -----------------------------------------------------------------------
PIN_RATE = 0.0025    # ~$0.21 + 0.05%  (simplified to 0.25%)
SIG_RATE = 0.0055    # ~$0.21 + 0.55%  (simplified to 0.55%)

acct_totals['pin_interchange'] = acct_totals['total_pin_dollars'] * PIN_RATE
acct_totals['sig_interchange'] = acct_totals['total_sig_dollars'] * SIG_RATE
acct_totals['total_interchange'] = (
    acct_totals['pin_interchange'] + acct_totals['sig_interchange']
)

# -----------------------------------------------------------------------
# 6. Opportunity: if ALL spend routed as SIG
# -----------------------------------------------------------------------
acct_totals['if_all_sig_interchange'] = total_spend * SIG_RATE
acct_totals['opportunity'] = (
    acct_totals['if_all_sig_interchange'] - acct_totals['total_interchange']
)

# Merge demographic fields for downstream analysis
demo_cols_desired = ['Prod Code', 'Prod Desc', 'Business?', 'Account Holder Age']
demo_cols_present = [c for c in demo_cols_desired if c in rewards_df.columns]
if demo_cols_present:
    demo = rewards_df[[acct_col] + demo_cols_present].copy()
    demo.columns = ['acct_number'] + demo_cols_present
    acct_totals = acct_totals.merge(demo, on='acct_number', how='left')

interchange_df = acct_totals.copy()

# -----------------------------------------------------------------------
# 7. Monthly aggregates for trend charts
# -----------------------------------------------------------------------
monthly_interchange = monthly_long_df.groupby('month').agg(
    pin_dollars=('pin_dollars', 'sum'),
    sig_dollars=('sig_dollars', 'sum'),
    pin_count=('pin_count', 'sum'),
    sig_count=('sig_count', 'sum'),
).reset_index()

# Preserve chronological order
month_order_map = {label: idx for idx, label in enumerate(MONTH_LABELS)}
monthly_interchange['sort_key'] = monthly_interchange['month'].map(month_order_map)
monthly_interchange.sort_values('sort_key', inplace=True)
monthly_interchange.drop(columns='sort_key', inplace=True)
monthly_interchange.reset_index(drop=True, inplace=True)

# Add interchange estimates per month
monthly_interchange['pin_ic'] = monthly_interchange['pin_dollars'] * PIN_RATE
monthly_interchange['sig_ic'] = monthly_interchange['sig_dollars'] * SIG_RATE
monthly_interchange['total_ic'] = monthly_interchange['pin_ic'] + monthly_interchange['sig_ic']

total_spend_monthly = monthly_interchange['pin_dollars'] + monthly_interchange['sig_dollars']
monthly_interchange['sig_ratio'] = np.where(
    total_spend_monthly > 0,
    monthly_interchange['sig_dollars'] / total_spend_monthly,
    0
)

# -----------------------------------------------------------------------
# 8. Summary
# -----------------------------------------------------------------------
total_ic = interchange_df['total_interchange'].sum()
total_pin_ic = interchange_df['pin_interchange'].sum()
total_sig_ic = interchange_df['sig_interchange'].sum()
total_opp = interchange_df['opportunity'].sum()
overall_sig_ratio = (
    interchange_df['total_sig_dollars'].sum()
    / (interchange_df['total_pin_dollars'].sum() + interchange_df['total_sig_dollars'].sum())
)

num_months = len(MONTH_LABELS)
annualization_factor = 12.0 / num_months if num_months > 0 else 1.0

print(f"\n{'='*60}")
print(f"INTERCHANGE SUMMARY  ({num_months} months of data)")
print(f"{'='*60}")
print(f"  Estimated Total Interchange : ${total_ic:,.0f}")
print(f"    PIN component              : ${total_pin_ic:,.0f}  ({total_pin_ic/total_ic*100:.1f}%)")
print(f"    SIG component              : ${total_sig_ic:,.0f}  ({total_sig_ic/total_ic*100:.1f}%)")
print(f"  Overall SIG Ratio            : {overall_sig_ratio:.1%}")
print(f"  Annualized Interchange       : ${total_ic * annualization_factor:,.0f}")
print(f"  Theoretical Max (all SIG)    : ${interchange_df['if_all_sig_interchange'].sum():,.0f}")
print(f"  Total Opportunity Gap        : ${total_opp:,.0f}")
print(f"  Accounts with data           : {len(interchange_df):,}")
print(f"{'='*60}")
