# ===========================================================================
# PAYROLL DISTRIBUTION: Payroll vs Non-Payroll Side-by-Side Comparison
# ===========================================================================
# Grouped bar chart comparing payroll members against non-payroll on
# key metrics. Shows the multiplier effect of payroll/PFI membership.

fig, ax = plt.subplots(figsize=(16, 8))

# ---------------------------------------------------------------------------
# Compute comparison metrics
# ---------------------------------------------------------------------------
pr = payroll_df[payroll_df['has_payroll']].copy()
non_pr = payroll_df[~payroll_df['has_payroll']].copy()

metrics = {}
labels = []

# Avg balance
bal_col = None
for col_name in ['avg_balance', 'curr_balance']:
    if col_name in payroll_df.columns:
        bal_col = col_name
        break

if bal_col:
    metrics['Avg Balance'] = (pr[bal_col].mean(), non_pr[bal_col].mean())
    labels.append('Avg Balance')

# Avg monthly spend (total debit / months)
if 'total_debit' in payroll_df.columns:
    n_months = max(DATASET_MONTHS, 1) if 'DATASET_MONTHS' in dir() or 'DATASET_MONTHS' in globals() else 1
    pr_monthly = abs(pr['total_debit'].mean()) / n_months
    non_pr_monthly = abs(non_pr['total_debit'].mean()) / n_months
    metrics['Avg Monthly Spend'] = (pr_monthly, non_pr_monthly)
    labels.append('Avg Monthly Spend')

# Avg tenure (account age in days -> years)
if 'account_age_days' in payroll_df.columns:
    pr_tenure = pr['account_age_days'].mean() / 365.25
    non_pr_tenure = non_pr['account_age_days'].mean() / 365.25
    metrics['Avg Tenure (yrs)'] = (pr_tenure, non_pr_tenure)
    labels.append('Avg Tenure (yrs)')

# Avg transaction count
if 'total_txn_count' in payroll_df.columns:
    metrics['Avg Txn Count'] = (pr['total_txn_count'].mean(), non_pr['total_txn_count'].mean())
    labels.append('Avg Txn Count')

# Fallback: ensure we have at least some metrics
if len(metrics) == 0:
    metrics['Avg Txn Count'] = (
        pr['total_txn_count'].mean() if 'total_txn_count' in pr.columns else 0,
        non_pr['total_txn_count'].mean() if 'total_txn_count' in non_pr.columns else 0,
    )
    labels.append('Avg Txn Count')

# ---------------------------------------------------------------------------
# Normalize to non-payroll = 100 (index) for clean side-by-side
# ---------------------------------------------------------------------------
payroll_vals = []
non_payroll_vals = []
multipliers = []

for lbl in labels:
    pr_v, npr_v = metrics[lbl]
    payroll_vals.append(pr_v)
    non_payroll_vals.append(npr_v)
    mult = pr_v / npr_v if npr_v > 0 else 0
    multipliers.append(mult)

x = np.arange(len(labels))
width = 0.35

bars_pr = ax.bar(x - width / 2, payroll_vals, width,
                 label='Payroll Members', color=GEN_COLORS['accent'],
                 edgecolor='white', linewidth=1.5, zorder=3)
bars_npr = ax.bar(x + width / 2, non_payroll_vals, width,
                  label='Non-Payroll Members', color=GEN_COLORS['info'],
                  edgecolor='white', linewidth=1.5, zorder=3)

# Add multiplier annotations above payroll bars
for i, (bar, mult) in enumerate(zip(bars_pr, multipliers)):
    y_pos = bar.get_height()
    ax.text(bar.get_x() + bar.get_width() / 2, y_pos * 1.02,
            f"{mult:.1f}x",
            ha='center', va='bottom', fontsize=16, fontweight='bold',
            color=GEN_COLORS['accent'])

# Add value labels on both bar sets
for bar_set, vals in [(bars_pr, payroll_vals), (bars_npr, non_payroll_vals)]:
    for bar, val in zip(bar_set, vals):
        y_pos = bar.get_height()
        if val >= 1000:
            label = f"{val:,.0f}"
        elif val >= 1:
            label = f"{val:.1f}"
        else:
            label = f"{val:.2f}"
        ax.text(bar.get_x() + bar.get_width() / 2, y_pos * 0.5,
                label, ha='center', va='center', fontsize=11,
                fontweight='bold', color='white')

ax.set_xticks(x)
ax.set_xticklabels(labels, fontsize=14, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_count))
ax.legend(fontsize=14, loc='upper right')

gen_clean_axes(ax)

ax.set_title("Payroll vs Non-Payroll Members: Key Metrics",
             fontsize=24, fontweight='bold', color=GEN_COLORS['dark_text'],
             loc='left', pad=20)
ax.text(0.0, 1.04,
        f"Payroll members consistently outperform  --  {DATASET_LABEL}",
        fontsize=13, style='italic', color=GEN_COLORS['muted'],
        transform=ax.transAxes)

plt.tight_layout()
plt.show()

# Print the multiplier summary
print("\nPayroll Multiplier Effect:")
for lbl, mult in zip(labels, multipliers):
    print(f"  {lbl}: {mult:.2f}x")
