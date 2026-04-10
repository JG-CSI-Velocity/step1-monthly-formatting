# ===========================================================================
# LEAKAGE OPPORTUNITY: External Financial Services (Conference Edition)
# ===========================================================================
# If finserv data exists: members using external financial services that
# the credit union could capture. Bar chart of leakage categories.

if 'rel_df' not in dir() or len(rel_df) == 0:
    print("    No relationship data available. Skipping leakage analysis.")
elif not HAS_FINSERV:
    print("    Financial services leakage data not available.")
    print("    Run the finserv analysis folder first to identify external services.")
    print("    Skipping leakage opportunity chart.")
else:
    # ------------------------------------------------------------------
    # Build leakage summary from finserv data
    # ------------------------------------------------------------------
    leakage_rows = []

    finserv_source = None
    if 'finserv_summary_df' in dir() and len(finserv_summary_df) > 0:
        finserv_source = 'summary'
    elif 'financial_services_data' in dir() and len(financial_services_data) > 0:
        finserv_source = 'detail'

    if finserv_source == 'summary':
        for _, row in finserv_summary_df.iterrows():
            cat_name = row.get('category', row.get('Category', 'Unknown'))
            acct_count = row.get('unique_accounts', row.get('Accounts', 0))
            txn_count = row.get('total_transactions', row.get('Transactions', 0))
            leakage_rows.append({
                'category': cat_name,
                'account_count': acct_count,
                'transaction_count': txn_count,
            })
    elif finserv_source == 'detail':
        for category, data in financial_services_data.items():
            txns = data.get('transactions', pd.DataFrame())
            if len(txns) > 0:
                acct_count = txns['primary_account_num'].nunique()
                txn_count = len(txns)
                total_spend = txns['amount'].sum() if 'amount' in txns.columns else 0
            else:
                acct_count = 0
                txn_count = 0
                total_spend = 0
            leakage_rows.append({
                'category': category,
                'account_count': acct_count,
                'transaction_count': txn_count,
                'total_spend': total_spend,
            })

    if len(leakage_rows) == 0:
        print("    No leakage data found. Skipping.")
    else:
        leakage_df = pd.DataFrame(leakage_rows).sort_values(
            'account_count', ascending=True
        )

        # Exclude categories with zero accounts
        leakage_df = leakage_df[leakage_df['account_count'] > 0]

        if len(leakage_df) == 0:
            print("    All leakage categories have zero accounts. Skipping.")
        else:
            fig, ax = plt.subplots(figsize=(14, max(7, len(leakage_df) * 0.7 + 2)))

            n = len(leakage_df)
            bar_colors = [plt.cm.ScalarMappable(
                cmap=LinearSegmentedColormap.from_list(
                    'leakage', [GEN_COLORS['info'], GEN_COLORS['accent']]
                ),
                norm=plt.Normalize(0, max(n - 1, 1))
            ).to_rgba(i) for i in range(n)]

            bars = ax.barh(
                range(n), leakage_df['account_count'],
                color=bar_colors, edgecolor='white', linewidth=1.5,
                height=0.65, zorder=3
            )

            ax.set_yticks(range(n))
            ax.set_yticklabels(
                leakage_df['category'], fontsize=13, fontweight='bold'
            )

            max_val = leakage_df['account_count'].max()
            total_leakage_accts = leakage_df['account_count'].sum()

            for j, (_, row) in enumerate(leakage_df.iterrows()):
                label_parts = [f"{int(row['account_count']):,} members"]
                if 'total_spend' in row and row.get('total_spend', 0) > 0:
                    label_parts.append(f"${row['total_spend']:,.0f}")
                ax.text(
                    row['account_count'] + max_val * 0.015, j,
                    '  |  '.join(label_parts),
                    va='center', fontsize=14, fontweight='bold',
                    color=GEN_COLORS['dark_text']
                )

            ax.set_xlabel("Members Using External Services", fontsize=14,
                           fontweight='bold', labelpad=10)
            ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))
            ax.set_xlim(0, max_val * 1.4)

            gen_clean_axes(ax, keep_left=True, keep_bottom=True)
            ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
            ax.set_axisbelow(True)

            ax.set_title("Where Are Members Leaking to Competitors?",
                         fontsize=26, fontweight='bold',
                         color=GEN_COLORS['dark_text'], pad=35, loc='left')
            ax.text(0.0, 1.02,
                    f"{total_leakage_accts:,} members using external financial services  |  {DATASET_LABEL}",
                    transform=ax.transAxes, fontsize=14,
                    color=GEN_COLORS['accent'], style='italic', fontweight='bold')

            # Opportunity callout
            top_leak = leakage_df.iloc[-1]
            ax.text(0.98, 0.05,
                    f"Top opportunity: {top_leak['category']}\n"
                    f"{int(top_leak['account_count']):,} members to recapture",
                    transform=ax.transAxes, fontsize=13, fontweight='bold',
                    color=GEN_COLORS['primary'], ha='right', va='bottom',
                    bbox=dict(boxstyle='round,pad=0.5', facecolor=GEN_COLORS['light_bg'],
                              edgecolor=GEN_COLORS['primary'], alpha=0.9))

            plt.tight_layout()
            plt.show()
