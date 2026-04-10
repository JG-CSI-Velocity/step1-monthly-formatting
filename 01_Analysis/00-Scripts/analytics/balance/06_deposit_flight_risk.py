# ===========================================================================
# DEPOSIT FLIGHT RISK: High-Balance Declining Accounts (Conference Edition)
# ===========================================================================
# Filter $25K+ accounts with declining balances. Cross-ref competitor activity.
# Bar chart of risk magnitude + table of top 20 highest-balance decliners.

# ---------------------------------------------------------------------------
# Identify high-balance accounts with declining deposits
# ---------------------------------------------------------------------------
HIGH_BAL_THRESHOLD = 25_000

high_bal = balance_df[balance_df['Curr Bal'] >= HIGH_BAL_THRESHOLD].copy()
flight_risk = high_bal[high_bal['bal_delta'] < 0].copy()
flight_risk['abs_decline'] = flight_risk['bal_delta'].abs()
flight_risk = flight_risk.sort_values('abs_decline', ascending=False)

total_at_risk_deposits = flight_risk['Curr Bal'].sum()
total_decline_amount = flight_risk['abs_decline'].sum()
risk_count = len(flight_risk)

# Check for competitor activity on at-risk accounts
has_competitor = 'competitor_spend_pct' in flight_risk.columns

# ---------------------------------------------------------------------------
# Bar chart: flight risk by balance band
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(16, 7),
                          gridspec_kw={'width_ratios': [1, 1]})

# Left panel: count + deposits at risk by band
risk_bands = flight_risk.groupby('balance_band', observed=False).agg(
    risk_count=('Acct Number', 'count'),
    deposits_at_risk=('Curr Bal', 'sum'),
    total_decline=('abs_decline', 'sum')
).reindex(BALANCE_BAND_ORDER).fillna(0)

# Only keep bands >= $25K
risk_bands = risk_bands.loc[['$25K-100K', '$100K+']]

colors_risk = [bal_band_palette.get(b, GEN_COLORS['muted']) for b in risk_bands.index]

bars = axes[0].barh(risk_bands.index, risk_bands['risk_count'],
                    color=colors_risk, edgecolor='white', linewidth=1.5, height=0.5)

for bar, (band, row) in zip(bars, risk_bands.iterrows()):
    if row['risk_count'] > 0:
        axes[0].text(bar.get_width() + risk_bands['risk_count'].max() * 0.03,
                     bar.get_y() + bar.get_height() / 2,
                     f"{int(row['risk_count']):,} accts | "
                     f"{gen_fmt_dollar(row['deposits_at_risk'], None)} at risk",
                     ha='left', va='center', fontsize=12, fontweight='bold',
                     color=GEN_COLORS['dark_text'])

axes[0].set_title("Accounts with Declining Balances",
                   fontsize=18, fontweight='bold', loc='left',
                   color=GEN_COLORS['dark_text'])
axes[0].set_xlabel("Number of Accounts", fontsize=13)
axes[0].xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_count))
axes[0].set_xlim(0, risk_bands['risk_count'].max() * 1.8 if risk_bands['risk_count'].max() > 0 else 10)
gen_clean_axes(axes[0])

# Right panel: competitor overlap (if available)
if has_competitor and len(flight_risk) > 0:
    comp_threshold = 20
    with_comp = flight_risk[flight_risk['competitor_spend_pct'] >= comp_threshold]
    without_comp = flight_risk[flight_risk['competitor_spend_pct'] < comp_threshold]

    comp_data = pd.DataFrame({
        'Category': [f'Competitor Activity\n(>={comp_threshold}% spend)', 'No Competitor Signal'],
        'Count': [len(with_comp), len(without_comp)],
        'Deposits': [with_comp['Curr Bal'].sum(), without_comp['Curr Bal'].sum()],
    })

    comp_colors = [GEN_COLORS['accent'], GEN_COLORS['muted']]
    bars2 = axes[1].barh(comp_data['Category'], comp_data['Count'],
                         color=comp_colors, edgecolor='white', linewidth=1.5, height=0.5)

    for bar, (_, row) in zip(bars2, comp_data.iterrows()):
        if row['Count'] > 0:
            axes[1].text(bar.get_width() + comp_data['Count'].max() * 0.03,
                         bar.get_y() + bar.get_height() / 2,
                         f"{int(row['Count']):,} | {gen_fmt_dollar(row['Deposits'], None)}",
                         ha='left', va='center', fontsize=12, fontweight='bold',
                         color=GEN_COLORS['dark_text'])

    axes[1].set_title("Competitor Cross-Reference",
                       fontsize=18, fontweight='bold', loc='left',
                       color=GEN_COLORS['dark_text'])
    axes[1].set_xlabel("Number of Accounts", fontsize=13)
    axes[1].set_xlim(0, comp_data['Count'].max() * 1.8 if comp_data['Count'].max() > 0 else 10)
else:
    axes[1].text(0.5, 0.5, "No competitor data available\nfor cross-reference",
                 transform=axes[1].transAxes, ha='center', va='center',
                 fontsize=14, color=GEN_COLORS['muted'], style='italic')
    axes[1].set_title("Competitor Cross-Reference",
                       fontsize=18, fontweight='bold', loc='left',
                       color=GEN_COLORS['dark_text'])
    axes[1].axis('off')

gen_clean_axes(axes[1])

fig.suptitle("Deposit Flight Risk Analysis",
             fontsize=26, fontweight='bold',
             color=GEN_COLORS['dark_text'], y=1.03)
fig.text(0.01, 1.00,
         f"High-balance accounts ($25K+) with Curr Bal < Avg Bal | {DATASET_LABEL}",
         fontsize=12, style='italic', color=GEN_COLORS['muted'])

plt.tight_layout()
plt.show()

# ---------------------------------------------------------------------------
# Top 20 highest-balance declining accounts table
# ---------------------------------------------------------------------------
top20_risk = flight_risk.head(20).copy()
table_cols = ['Acct Number', 'Curr Bal', 'Avg Bal', 'bal_delta', 'balance_band']
if has_competitor:
    table_cols.append('competitor_spend_pct')
if 'txn_count' in top20_risk.columns:
    table_cols.append('txn_count')

available_table_cols = [c for c in table_cols if c in top20_risk.columns]
display_risk = top20_risk[available_table_cols].copy()

format_dict = {
    'Curr Bal': '${:,.0f}',
    'Avg Bal': '${:,.0f}',
    'bal_delta': '${:,.0f}',
}
if has_competitor:
    format_dict['competitor_spend_pct'] = '{:.1f}%'
if 'txn_count' in available_table_cols:
    format_dict['txn_count'] = '{:,.0f}'

styled_risk = (
    display_risk.style
    .hide(axis='index')
    .format(format_dict)
    .set_properties(**{
        'font-size': '12px', 'text-align': 'center',
        'border': '1px solid #E9ECEF', 'padding': '6px 10px',
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', GEN_COLORS['accent']),
            ('color', 'white'), ('font-size', '13px'),
            ('font-weight', 'bold'), ('text-align', 'center'),
            ('padding', '8px 10px'),
        ]},
        {'selector': 'caption', 'props': [
            ('font-size', '18px'), ('font-weight', 'bold'),
            ('color', GEN_COLORS['dark_text']), ('text-align', 'left'),
            ('padding-bottom', '10px'),
        ]},
    ])
    .set_caption("Top 20 Highest-Balance Declining Accounts")
)

display(styled_risk)

print(f"\n    INSIGHT: {risk_count:,} high-balance accounts ($25K+) show declining deposits.")
print(f"    INSIGHT: {gen_fmt_dollar(total_at_risk_deposits, None)} in current deposits at risk.")
print(f"    INSIGHT: These accounts have declined by "
      f"{gen_fmt_dollar(total_decline_amount, None)} from their average balance.")
