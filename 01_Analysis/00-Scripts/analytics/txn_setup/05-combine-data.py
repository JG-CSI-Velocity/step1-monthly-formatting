# Combine all dataframes (skip if loaded from Parquet cache)
if not SKIP_COMBINE:
    if not transaction_files:
        raise ValueError(
            f"No transaction files loaded for client {CLIENT_ID}. "
            f"Check that TXN files exist in: {CLIENT_PATH}"
        )

    combined_df = pd.concat(transaction_files, ignore_index=True)

    # Free the individual DataFrames -- combined_df has the data now
    del transaction_files
    gc.collect()

    # Convert data types -- coerce handles non-numeric values like "N/A" or stray headers
    combined_df['amount'] = pd.to_numeric(combined_df['amount'], errors='coerce')
    _bad_amounts = combined_df['amount'].isna().sum()
    if _bad_amounts > 0:
        print(f"WARNING: {_bad_amounts:,} rows with non-numeric amount values (set to NaN)")
    if combined_df['amount'].median() < 0:
        combined_df['amount'] = combined_df['amount'].abs()

    # Parse transaction_date to datetime (format: MM/DD/YYYY)
    combined_df['transaction_date'] = pd.to_datetime(
        combined_df['transaction_date'], format='mixed', dayfirst=False
    )

    # Convert low-cardinality strings to categoricals now (before merchant consolidation)
    # This makes the string ops in 07-consolidation-summary much faster
    for _cat_col in ['transaction_type', 'card_present', 'transaction_code', 'institution', 'source_file']:
        if _cat_col in combined_df.columns:
            combined_df[_cat_col] = combined_df[_cat_col].astype('category')

# Dataset overview (runs for both cache and fresh builds)
print(f"Combined Dataset Overview:")
print(f"{'='*50}")
print(f"Total Shape: {combined_df.shape}")
print(f"Total Transactions: {len(combined_df):,}")
print(f"Total Columns: {combined_df.shape[1]}")
print(f"Memory Usage: {combined_df.memory_usage(deep=True).sum() / 1024**2:.0f} MB")
_dt_min = combined_df['transaction_date'].min()
_dt_max = combined_df['transaction_date'].max()
if pd.notna(_dt_min) and pd.notna(_dt_max):
    print(f"\nDate Range: {_dt_min.strftime('%b %d, %Y')} to {_dt_max.strftime('%b %d, %Y')}")
else:
    print(f"\nDate Range: could not determine (check transaction_date parsing)")
print(f"Unique Accounts: {combined_df['primary_account_num'].nunique():,}")
print(f"Unique Merchants: {combined_df['merchant_name'].nunique():,}")
print(f"Total Transactions Value: {combined_df['amount'].sum():,.0f}")
