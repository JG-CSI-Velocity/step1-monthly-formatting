# ===========================================================================
# PRODUCT DATA: Master Aggregation Pipeline (Conference Edition)
# ===========================================================================
# Merges Prod Code + Prod Desc from rewards_df onto combined_df.
# Builds: prod_agg, prod_monthly. Guard: try/except for missing columns.

try:
    # Merge product info onto combined_df
    prod_subset = rewards_df[['Acct Number', 'Prod Code', 'Prod Desc']].copy()
    prod_subset.columns = ['account_number', 'prod_code', 'prod_desc']
    prod_subset['account_number'] = prod_subset['account_number'].astype(str).str.strip()

    # Drop stale merge columns if re-running
    for col in ['prod_code', 'prod_desc']:
        if col in combined_df.columns:
            combined_df.drop(columns=col, inplace=True)

    prod_merged = combined_df.merge(
        prod_subset,
        left_on='primary_account_num',
        right_on='account_number',
        how='left'
    ).drop(columns='account_number')

    # Store on combined_df for other folders
    combined_df['prod_code'] = prod_merged['prod_code']
    combined_df['prod_desc'] = prod_merged['prod_desc']

    # Create clean product label
    prod_merged['product_label'] = prod_merged.apply(
        lambda r: f"{r['prod_code']} - {r['prod_desc']}" if pd.notna(r['prod_code']) and pd.notna(r['prod_desc'])
        else str(r['prod_code']) if pd.notna(r['prod_code'])
        else 'Unknown', axis=1
    )

    prod_df = prod_merged[prod_merged['product_label'] != 'Unknown'].copy()

    if len(prod_df) == 0:
        print("    All product values are null. Skipping product analysis.")
        prod_agg = pd.DataFrame()
    else:
        # -----------------------------------------------------------------------
        # Core product aggregation
        # -----------------------------------------------------------------------
        prod_agg = prod_df.groupby('product_label').agg(
            txn_count=('transaction_date', 'count'),
            unique_accounts=('primary_account_num', 'nunique'),
            total_spend=('amount', 'sum'),
            avg_spend=('amount', 'mean'),
            median_spend=('amount', 'median'),
        ).reset_index()

        total_txns_prod = len(prod_df)
        total_accts_prod = prod_df['primary_account_num'].nunique()

        prod_agg['txn_pct'] = prod_agg['txn_count'] / total_txns_prod * 100
        prod_agg['spend_pct'] = prod_agg['total_spend'] / prod_agg['total_spend'].sum() * 100
        prod_agg['acct_pct'] = prod_agg['unique_accounts'] / total_accts_prod * 100
        prod_agg['txn_per_account'] = prod_agg['txn_count'] / prod_agg['unique_accounts']
        prod_agg = prod_agg.sort_values('txn_count', ascending=False).reset_index(drop=True)
        prod_agg['rank'] = range(1, len(prod_agg) + 1)

        # -----------------------------------------------------------------------
        # Monthly trend by product
        # -----------------------------------------------------------------------
        top5_products = prod_agg.head(5)['product_label'].tolist()
        prod_monthly = prod_df[prod_df['product_label'].isin(top5_products)].groupby(
            ['year_month', 'product_label']
        ).agg(txn_count=('transaction_date', 'count')).reset_index()

        prod_month_totals = prod_df.groupby('year_month').size().reset_index(name='month_total')
        prod_monthly = prod_monthly.merge(prod_month_totals, on='year_month')
        prod_monthly['share_pct'] = prod_monthly['txn_count'] / prod_monthly['month_total'] * 100

        # -----------------------------------------------------------------------
        # Conference-styled product summary table
        # -----------------------------------------------------------------------
        prod_display = prod_agg[['rank', 'product_label', 'txn_count', 'txn_pct',
                                  'unique_accounts', 'total_spend', 'txn_per_account']].copy()
        prod_display.columns = ['Rank', 'Product', 'Transactions', 'Txn %',
                                 'Accounts', 'Total Spend', 'Txns/Acct']
        prod_display['Product'] = prod_display['Product'].str[:40]

        styled = (
            prod_display.style
            .hide(axis='index')
            .format({
                'Rank': '{:.0f}',
                'Transactions': '{:,.0f}',
                'Txn %': '{:.1f}%',
                'Accounts': '{:,.0f}',
                'Total Spend': '${:,.0f}',
                'Txns/Acct': '{:.1f}',
            })
            .set_properties(**{
                'font-size': '13px', 'font-weight': 'bold',
                'text-align': 'center', 'border': '1px solid #E9ECEF',
                'padding': '7px 10px',
            })
            .set_table_styles([
                {'selector': 'th', 'props': [
                    ('background-color', GEN_COLORS['primary']),
                    ('color', 'white'), ('font-size', '14px'),
                    ('font-weight', 'bold'), ('text-align', 'center'),
                    ('padding', '8px 10px'),
                ]},
                {'selector': 'caption', 'props': [
                    ('font-size', '22px'), ('font-weight', 'bold'),
                    ('color', GEN_COLORS['dark_text']), ('text-align', 'left'),
                    ('padding-bottom', '12px'),
                ]},
            ])
            .set_caption("Card Products by Transaction Volume")
            .bar(subset=['Transactions'], color=GEN_COLORS['info'], vmin=0)
        )

        display(styled)

        print(f"\n    {len(prod_agg)} distinct products")
        print(f"    Dominant product: {prod_agg.iloc[0]['product_label'][:35]} ({prod_agg.iloc[0]['txn_pct']:.1f}%)")
        print(f"    {total_accts_prod:,} accounts matched to products")

except (NameError, KeyError) as e:
    print(f"    Product data not available: {e}")
    print("    Skipping product analysis.")
    prod_agg = pd.DataFrame()
