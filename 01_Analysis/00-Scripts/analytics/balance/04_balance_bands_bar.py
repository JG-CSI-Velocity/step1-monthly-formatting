# ===========================================================================
# BALANCE BANDS: Account Count + Deposit Concentration (Conference Edition)
# ===========================================================================
# Horizontal bars for account count, with deposit % annotations.
# Pareto annotation for top band concentration.

fig, ax = plt.subplots(figsize=(14, 7))

# Aggregate by balance band
band_stats = balance_df.groupby('balance_band', observed=False).agg(
    account_count=('Acct Number', 'count'),
    total_deposits=('Curr Bal', 'sum')
).reindex(BALANCE_BAND_ORDER)

band_stats['acct_pct'] = band_stats['account_count'] / band_stats['account_count'].sum() * 100
band_stats['deposit_pct'] = np.where(
    band_stats['total_deposits'].sum() > 0,
    band_stats['total_deposits'] / band_stats['total_deposits'].sum() * 100,
    0
)
band_stats['cum_deposit_pct'] = band_stats['deposit_pct'].cumsum()

# Reverse for horizontal bar (top band at top)
band_display = band_stats.iloc[::-1]

# ---------------------------------------------------------------------------
# Horizontal bar: account counts
# ---------------------------------------------------------------------------
colors = [bal_band_palette.get(b, GEN_COLORS['muted']) for b in band_display.index]
bars = ax.barh(band_display.index, band_display['account_count'],
               color=colors, edgecolor='white', linewidth=1.5, height=0.65)

# Annotate each bar with account count + deposit %
for bar, (band, row) in zip(bars, band_display.iterrows()):
    width = bar.get_width()
    # Account count label at end of bar
    ax.text(width + band_stats['account_count'].max() * 0.02,
            bar.get_y() + bar.get_height() / 2,
            f"{int(row['account_count']):,} accts  |  "
            f"{row['deposit_pct']:.1f}% of deposits",
            ha='left', va='center', fontsize=12, fontweight='bold',
            color=GEN_COLORS['dark_text'])

# ---------------------------------------------------------------------------
# Pareto annotation: top band
# ---------------------------------------------------------------------------
top_band = band_stats.index[-1]
top_band_deposit_pct = band_stats.loc[top_band, 'deposit_pct']
top_band_acct_pct = band_stats.loc[top_band, 'acct_pct']

ax.set_title("Balance Band Distribution",
             fontsize=24, fontweight='bold', loc='left',
             color=GEN_COLORS['dark_text'], pad=20)
ax.text(0.0, 1.03,
        f"Pareto: {top_band} accounts = {top_band_acct_pct:.1f}% of members "
        f"but hold {top_band_deposit_pct:.1f}% of all deposits | {DATASET_LABEL}",
        transform=ax.transAxes, fontsize=12, style='italic',
        color=GEN_COLORS['muted'])

ax.set_xlabel("Number of Accounts", fontsize=14)
ax.xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_count))
ax.set_xlim(0, band_stats['account_count'].max() * 1.55)

gen_clean_axes(ax)

plt.tight_layout()
plt.show()

# ---------------------------------------------------------------------------
# Concentration summary
# ---------------------------------------------------------------------------
top_two = band_stats.tail(2)
top_two_deposit_pct = top_two['deposit_pct'].sum()
top_two_acct_pct = top_two['acct_pct'].sum()

print(f"\n    INSIGHT: Top 2 balance bands ({', '.join(top_two.index)}) hold "
      f"{top_two_deposit_pct:.1f}% of deposits with only "
      f"{top_two_acct_pct:.1f}% of accounts.")
print(f"    INSIGHT: {band_stats.loc['$0', 'account_count']:,} accounts "
      f"({band_stats.loc['$0', 'acct_pct']:.1f}%) at $0 -- "
      f"reactivation target for deposit growth.")
