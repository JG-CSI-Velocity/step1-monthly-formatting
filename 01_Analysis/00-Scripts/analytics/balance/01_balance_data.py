# ===========================================================================
# BALANCE DATA: Master Aggregation Pipeline (Conference Edition)
# ===========================================================================
# Builds: balance_df with bands, deltas, transaction activity merge,
# and bal_band_palette for consistent coloring.

# ---------------------------------------------------------------------------
# Extract and clean balance fields from rewards_df
# ---------------------------------------------------------------------------
balance_cols = ['Acct Number', 'Avg Bal', 'Curr Bal', 'Account Holder Age',
                'Account Age', 'Prod Code', 'Prod Desc', 'Business?', 'Branch']

available_cols = [c for c in balance_cols if c in rewards_df.columns]
balance_df = rewards_df[available_cols].copy()

# Convert balances to numeric (handle non-numeric gracefully)
for col in ['Avg Bal', 'Curr Bal']:
    if col in balance_df.columns:
        balance_df[col] = pd.to_numeric(
            balance_df[col].astype(str).str.replace(r'[,$]', '', regex=True),
            errors='coerce'
        ).fillna(0)

# ---------------------------------------------------------------------------
# Balance bands
# ---------------------------------------------------------------------------
BALANCE_BAND_ORDER = ['$0', '$1-1K', '$1K-5K', '$5K-25K', '$25K-100K', '$100K+']

def assign_balance_band(val):
    if val <= 0:
        return '$0'
    elif val < 1_000:
        return '$1-1K'
    elif val < 5_000:
        return '$1K-5K'
    elif val < 25_000:
        return '$5K-25K'
    elif val < 100_000:
        return '$25K-100K'
    else:
        return '$100K+'

if 'Curr Bal' in balance_df.columns:
    balance_df['balance_band'] = balance_df['Curr Bal'].apply(assign_balance_band)
    balance_df['balance_band'] = pd.Categorical(
        balance_df['balance_band'],
        categories=BALANCE_BAND_ORDER,
        ordered=True
    )

# ---------------------------------------------------------------------------
# Balance delta: positive = growing deposits, negative = declining
# ---------------------------------------------------------------------------
if 'Avg Bal' in balance_df.columns and 'Curr Bal' in balance_df.columns:
    balance_df['bal_delta'] = balance_df['Curr Bal'] - balance_df['Avg Bal']

# ---------------------------------------------------------------------------
# Merge transaction activity from combined_df
# ---------------------------------------------------------------------------
if 'Acct Number' in balance_df.columns:
    acct_activity = combined_df.groupby('primary_account_num').agg(
        txn_count=('transaction_date', 'count'),
        total_spend=('amount', 'sum')
    ).reset_index()

    balance_df = balance_df.merge(
        acct_activity,
        left_on='Acct Number',
        right_on='primary_account_num',
        how='left'
    )
    balance_df['txn_count'] = balance_df['txn_count'].fillna(0).astype(int)
    balance_df['total_spend'] = balance_df['total_spend'].fillna(0)

    if 'primary_account_num' in balance_df.columns:
        balance_df.drop(columns=['primary_account_num'], inplace=True)

# ---------------------------------------------------------------------------
# Merge competitor activity if available
# ---------------------------------------------------------------------------
if 'competitor_category' in combined_df.columns:
    comp_activity = combined_df[combined_df['competitor_category'].notna()].groupby(
        'primary_account_num'
    ).agg(
        competitor_txns=('transaction_date', 'count'),
        competitor_spend=('amount', 'sum')
    ).reset_index()

    balance_df = balance_df.merge(
        comp_activity,
        left_on='Acct Number',
        right_on='primary_account_num',
        how='left'
    )
    balance_df['competitor_txns'] = balance_df['competitor_txns'].fillna(0).astype(int)
    balance_df['competitor_spend'] = balance_df['competitor_spend'].fillna(0)
    if 'primary_account_num' in balance_df.columns:
        balance_df.drop(columns=['primary_account_num'], inplace=True)

    # Competitor spend percentage
    balance_df['competitor_spend_pct'] = np.where(
        balance_df['total_spend'] > 0,
        balance_df['competitor_spend'] / balance_df['total_spend'] * 100,
        0
    )

# ---------------------------------------------------------------------------
# Balance band palette (consistent coloring across all charts)
# ---------------------------------------------------------------------------
bal_band_palette = {
    '$0':        '#6C757D',
    '$1-1K':     '#A8DADC',
    '$1K-5K':    '#457B9D',
    '$5K-25K':   '#2EC4B6',
    '$25K-100K': '#FF9F1C',
    '$100K+':    '#E63946',
}

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
total_deposits = balance_df['Curr Bal'].sum() if 'Curr Bal' in balance_df.columns else 0
avg_balance = balance_df['Curr Bal'].mean() if 'Curr Bal' in balance_df.columns else 0
median_balance = balance_df['Curr Bal'].median() if 'Curr Bal' in balance_df.columns else 0
total_accounts = len(balance_df)
zero_bal_count = (balance_df['Curr Bal'] <= 0).sum() if 'Curr Bal' in balance_df.columns else 0
zero_bal_pct = zero_bal_count / total_accounts * 100 if total_accounts > 0 else 0

print("Balance data pipeline loaded.")
print(f"    {total_accounts:,} accounts")
print(f"    Total deposits: ${total_deposits:,.0f}")
print(f"    Average balance: ${avg_balance:,.0f}")
print(f"    Median balance: ${median_balance:,.0f}")
print(f"    Zero-balance accounts: {zero_bal_count:,} ({zero_bal_pct:.1f}%)")

if 'balance_band' in balance_df.columns:
    print(f"\n    Distribution by band:")
    band_dist = balance_df['balance_band'].value_counts().reindex(BALANCE_BAND_ORDER)
    for band, count in band_dist.items():
        pct = count / total_accounts * 100
        print(f"      {band:>12s}: {count:>6,} accounts ({pct:>5.1f}%)")
