# ===========================================================================
# BALANCE DISTRIBUTION: Histogram + Box Plot (Conference Edition)
# ===========================================================================
# Log-scale histogram for readability + box plot. Top 10% annotation.

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10),
                                gridspec_kw={'height_ratios': [3, 1]})

# Filter to positive balances for log scale
positive_bal = balance_df[balance_df['Curr Bal'] > 0]['Curr Bal'].copy()

# ---------------------------------------------------------------------------
# Top panel: histogram on log scale
# ---------------------------------------------------------------------------
if len(positive_bal) > 0:
    log_bins = np.logspace(
        np.log10(max(positive_bal.min(), 1)),
        np.log10(positive_bal.max()),
        50
    )
    ax1.hist(positive_bal, bins=log_bins,
             color=GEN_COLORS['info'], edgecolor='white',
             linewidth=0.5, alpha=0.85)
    ax1.set_xscale('log')

    # Annotate top 10% concentration
    top_10_threshold = positive_bal.quantile(0.90)
    top_10_deposits = positive_bal[positive_bal >= top_10_threshold].sum()
    top_10_pct = top_10_deposits / positive_bal.sum() * 100

    ax1.axvline(top_10_threshold, color=GEN_COLORS['accent'],
                linestyle='--', linewidth=2, alpha=0.8)
    ax1.text(top_10_threshold * 1.3,
             ax1.get_ylim()[1] * 0.85,
             f"Top 10% threshold: {gen_fmt_dollar(top_10_threshold, None)}\n"
             f"Hold {top_10_pct:.0f}% of all deposits",
             fontsize=13, fontweight='bold',
             color=GEN_COLORS['accent'],
             bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                       edgecolor=GEN_COLORS['accent'], alpha=0.9))

    ax1.xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_count))

ax1.set_title("Balance Distribution (Positive Balances, Log Scale)",
              fontsize=22, fontweight='bold', loc='left',
              color=GEN_COLORS['dark_text'])
ax1.set_xlabel("")
ax1.set_ylabel("Account Count", fontsize=14)
gen_clean_axes(ax1)

# Subtitle
ax1.text(0.0, 1.04, f"Excludes {zero_bal_count:,} zero-balance accounts | {DATASET_LABEL}",
         transform=ax1.transAxes, fontsize=12, style='italic',
         color=GEN_COLORS['muted'])

# ---------------------------------------------------------------------------
# Bottom panel: box plot
# ---------------------------------------------------------------------------
if len(positive_bal) > 0:
    bp = ax2.boxplot(positive_bal, vert=False, widths=0.6,
                     patch_artist=True,
                     boxprops=dict(facecolor=GEN_COLORS['info'], alpha=0.6),
                     medianprops=dict(color=GEN_COLORS['accent'], linewidth=2),
                     whiskerprops=dict(color=GEN_COLORS['primary']),
                     capprops=dict(color=GEN_COLORS['primary']),
                     flierprops=dict(marker='o', markerfacecolor=GEN_COLORS['muted'],
                                     markersize=3, alpha=0.3))
    ax2.set_xscale('log')
    ax2.xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))
    ax2.set_xlabel("Account Balance", fontsize=14)
    ax2.set_yticklabels([])

gen_clean_axes(ax2, keep_left=False)

plt.tight_layout()
plt.show()

print(f"\n    INSIGHT: Top 10% of depositors (balances above "
      f"{gen_fmt_dollar(top_10_threshold, None)}) hold "
      f"{top_10_pct:.0f}% of all deposits.")
print(f"    INSIGHT: {zero_bal_count:,} accounts ({zero_bal_pct:.1f}%) "
      f"carry zero balance -- opportunity for reactivation.")
