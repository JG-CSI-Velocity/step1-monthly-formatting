# ===========================================================================
# INTERCHANGE BY MERCHANT -- PIN/SIG SPLIT PER TOP MERCHANT
# ===========================================================================
# Join interchange account data with combined_df transaction-level data.
# Identify merchants with highest PIN usage = biggest conversion targets.

# -----------------------------------------------------------------------
# Check required columns
# -----------------------------------------------------------------------
has_merchant = ('merchant_consolidated' in combined_df.columns
                or 'merchant_name' in combined_df.columns)
has_amount = 'transaction_amount' in combined_df.columns

if not has_merchant:
    print("WARNING: No merchant column found in combined_df.")
    print("  Available columns:", combined_df.columns.tolist()[:20])

merchant_col = ('merchant_consolidated' if 'merchant_consolidated' in combined_df.columns
                else 'merchant_name' if 'merchant_name' in combined_df.columns
                else None)

# -----------------------------------------------------------------------
# Approach: Use account-level SIG ratios joined to transaction data
# to estimate per-merchant PIN/SIG routing behavior
# -----------------------------------------------------------------------
if merchant_col and has_amount:
    # Ensure numeric
    combined_df['transaction_amount'] = pd.to_numeric(
        combined_df['transaction_amount'], errors='coerce')

    # Get account-level sig ratio from interchange_df
    acct_sig = interchange_df[['acct_number', 'sig_ratio']].copy()
    acct_sig.columns = ['acct_number', 'acct_sig_ratio']

    # Find the account column in combined_df
    acct_join_col = None
    for candidate in ['primary_account_num', 'Acct Number', ' Acct Number',
                       'account_number', 'acct_number']:
        if candidate in combined_df.columns:
            acct_join_col = candidate
            break

    if acct_join_col:
        txn_merged = combined_df.merge(
            acct_sig,
            left_on=acct_join_col,
            right_on='acct_number',
            how='left'
        )
    else:
        txn_merged = combined_df.copy()
        txn_merged['acct_sig_ratio'] = np.nan

    # Aggregate by merchant
    merchant_agg = (
        txn_merged.groupby(merchant_col)
        .agg(
            total_dollars=('transaction_amount', 'sum'),
            txn_count=('transaction_amount', 'count'),
            avg_sig_ratio=('acct_sig_ratio', 'mean'),
        )
        .reset_index()
    )
    merchant_agg = merchant_agg[merchant_agg['total_dollars'] > 0]

    # Estimate PIN/SIG split per merchant using avg account sig ratio
    merchant_agg['est_sig_dollars'] = (
        merchant_agg['total_dollars'] * merchant_agg['avg_sig_ratio'].fillna(0.5))
    merchant_agg['est_pin_dollars'] = (
        merchant_agg['total_dollars'] - merchant_agg['est_sig_dollars'])

    # Interchange estimates
    merchant_agg['est_sig_ic'] = merchant_agg['est_sig_dollars'] * SIG_RATE
    merchant_agg['est_pin_ic'] = merchant_agg['est_pin_dollars'] * PIN_RATE
    merchant_agg['est_total_ic'] = merchant_agg['est_sig_ic'] + merchant_agg['est_pin_ic']

    # Opportunity: if all spend at SIG
    merchant_agg['est_opportunity'] = (
        merchant_agg['total_dollars'] * SIG_RATE - merchant_agg['est_total_ic'])

    # Top 20 by total dollars
    top20 = merchant_agg.nlargest(20, 'total_dollars').sort_values(
        'avg_sig_ratio', ascending=True)

    # -----------------------------------------------------------------------
    # Stacked horizontal bar: PIN$ vs SIG$ per merchant
    # -----------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(16, 9))

    y_pos = np.arange(len(top20))
    merchant_names = top20[merchant_col].values

    # Truncate long merchant names
    display_names = [n[:30] + '...' if len(str(n)) > 30 else str(n)
                     for n in merchant_names]

    bars_pin = ax.barh(y_pos, top20['est_pin_dollars'],
                       color=GEN_COLORS['accent'], alpha=0.85,
                       height=0.6, label='Estimated PIN $')
    bars_sig = ax.barh(y_pos, top20['est_sig_dollars'],
                       left=top20['est_pin_dollars'],
                       color=GEN_COLORS['info'], alpha=0.85,
                       height=0.6, label='Estimated SIG $')

    ax.set_yticks(y_pos)
    ax.set_yticklabels(display_names, fontsize=11)
    ax.set_xlabel('Transaction Dollars', fontsize=14, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))

    # SIG ratio annotation on right side
    for i, (_, row) in enumerate(top20.iterrows()):
        ratio = row['avg_sig_ratio']
        if pd.notna(ratio):
            color = (GEN_COLORS['success'] if ratio >= 0.60
                     else (GEN_COLORS['warning'] if ratio >= 0.40
                           else GEN_COLORS['accent']))
            ax.text(row['total_dollars'] * 1.01, i,
                    f"SIG: {ratio:.0%}",
                    va='center', fontsize=10, fontweight='bold', color=color)

    ax.legend(loc='lower right', fontsize=13)
    gen_clean_axes(ax)

    fig.suptitle("Top 20 Merchants -- PIN vs SIG Routing Estimate",
                 fontsize=24, fontweight='bold', x=0.02, ha='left',
                 color=GEN_COLORS['dark_text'])
    fig.text(0.02, 0.95,
             f"Grocery/retail with high PIN = biggest opportunity  |  {DATASET_LABEL}",
             fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
             ha='left')

    plt.tight_layout(rect=[0, 0, 1, 0.93])
    plt.show()

    # Summary table
    print(f"\nTop 10 Merchants by Opportunity (est.):")
    opp_top = merchant_agg.nlargest(10, 'est_opportunity')
    for _, row in opp_top.iterrows():
        print(f"  {row[merchant_col]:<30s}  "
              f"SIG Ratio: {row['avg_sig_ratio']:.0%}  "
              f"Opportunity: ${row['est_opportunity']:,.0f}")

else:
    print("Skipping merchant-level interchange analysis.")
    print("  Requires: merchant column + transaction_amount in combined_df")
    fig, ax = plt.subplots(figsize=(14, 7))
    ax.text(0.5, 0.5,
            'Merchant-level data not available\n'
            'Requires combined_df with merchant and transaction columns',
            ha='center', va='center', fontsize=16, color=GEN_COLORS['muted'],
            transform=ax.transAxes)
    ax.set_axis_off()
    fig.suptitle("Top Merchants -- PIN vs SIG Routing",
                 fontsize=24, fontweight='bold', x=0.02, ha='left',
                 color=GEN_COLORS['dark_text'])
    plt.tight_layout()
    plt.show()
