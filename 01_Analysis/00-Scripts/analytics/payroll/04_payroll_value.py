# ===========================================================================
# PAYROLL VALUE: Detailed Comparison Table + Multiplier Chart
# ===========================================================================
# Full dimension-by-dimension comparison of payroll vs non-payroll members.
# Styled table + horizontal bar chart of multipliers.

# ---------------------------------------------------------------------------
# 1. Build comprehensive comparison
# ---------------------------------------------------------------------------
pr = payroll_df[payroll_df['has_payroll']].copy()
non_pr = payroll_df[~payroll_df['has_payroll']].copy()

comparison_rows = []

def safe_mean(series):
    return series.mean() if len(series) > 0 else 0

def add_row(metric, pr_val, npr_val, fmt='number'):
    mult = pr_val / npr_val if npr_val > 0 else 0
    comparison_rows.append({
        'Metric': metric,
        'Payroll Members': pr_val,
        'Non-Payroll Members': npr_val,
        'Multiplier': mult,
        'fmt': fmt,
    })

# Account count
add_row('Account Count', len(pr), len(non_pr), fmt='int')

# Balance metrics
for col_name, label in [('avg_balance', 'Avg Balance'), ('curr_balance', 'Current Balance')]:
    if col_name in payroll_df.columns:
        add_row(label, safe_mean(pr[col_name]), safe_mean(non_pr[col_name]), fmt='dollar')

# Transaction activity
if 'total_txn_count' in payroll_df.columns:
    add_row('Total Txn Count', safe_mean(pr['total_txn_count']),
            safe_mean(non_pr['total_txn_count']), fmt='number')

# Monthly activity
n_months = max(DATASET_MONTHS, 1) if 'DATASET_MONTHS' in dir() or 'DATASET_MONTHS' in globals() else 1
if 'total_txn_count' in payroll_df.columns:
    add_row('Monthly Txn Count',
            safe_mean(pr['total_txn_count']) / n_months,
            safe_mean(non_pr['total_txn_count']) / n_months, fmt='number')

# Spend
if 'total_debit' in payroll_df.columns:
    add_row('Avg Total Spend',
            abs(safe_mean(pr['total_debit'])),
            abs(safe_mean(non_pr['total_debit'])), fmt='dollar')
    add_row('Avg Monthly Spend',
            abs(safe_mean(pr['total_debit'])) / n_months,
            abs(safe_mean(non_pr['total_debit'])) / n_months, fmt='dollar')

# Credits
if 'total_credit' in payroll_df.columns:
    add_row('Avg Total Credits',
            safe_mean(pr['total_credit']),
            safe_mean(non_pr['total_credit']), fmt='dollar')

# Merchant diversity
if 'distinct_merchants' in payroll_df.columns:
    add_row('Distinct Merchants',
            safe_mean(pr['distinct_merchants']),
            safe_mean(non_pr['distinct_merchants']), fmt='number')

# Tenure
if 'account_age_days' in payroll_df.columns:
    add_row('Tenure (years)',
            safe_mean(pr['account_age_days']) / 365.25,
            safe_mean(non_pr['account_age_days']) / 365.25, fmt='number')

# Age
if 'member_age' in payroll_df.columns:
    add_row('Avg Member Age',
            safe_mean(pr['member_age']),
            safe_mean(non_pr['member_age']), fmt='number')

# ---------------------------------------------------------------------------
# 2. Styled comparison table
# ---------------------------------------------------------------------------
comp_df = pd.DataFrame(comparison_rows)

# Format display columns
def fmt_val(row, col):
    val = row[col]
    f = row['fmt']
    if f == 'dollar':
        return f"${val:,.0f}"
    elif f == 'int':
        return f"{val:,.0f}"
    else:
        return f"{val:,.1f}"

display_df = comp_df.copy()
display_df['Payroll Members'] = comp_df.apply(lambda r: fmt_val(r, 'Payroll Members'), axis=1)
display_df['Non-Payroll Members'] = comp_df.apply(lambda r: fmt_val(r, 'Non-Payroll Members'), axis=1)
display_df['Multiplier'] = comp_df['Multiplier'].apply(lambda x: f"{x:.2f}x")
display_df = display_df[['Metric', 'Payroll Members', 'Non-Payroll Members', 'Multiplier']]

styled_comp = (
    display_df.style
    .hide(axis='index')
    .set_properties(**{
        'font-size': '13px', 'text-align': 'center',
        'border': '1px solid #E9ECEF', 'padding': '8px 12px',
    })
    .set_properties(subset=['Metric'], **{
        'font-weight': 'bold', 'text-align': 'left',
        'color': GEN_COLORS['primary'],
    })
    .set_properties(subset=['Multiplier'], **{
        'font-weight': 'bold', 'color': GEN_COLORS['accent'],
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', GEN_COLORS['primary']),
            ('color', 'white'), ('font-size', '14px'),
            ('font-weight', 'bold'), ('text-align', 'center'),
            ('padding', '8px 12px'),
        ]},
        {'selector': 'caption', 'props': [
            ('font-size', '22px'), ('font-weight', 'bold'),
            ('color', GEN_COLORS['dark_text']), ('text-align', 'left'),
            ('padding-bottom', '12px'),
        ]},
    ])
    .set_caption("Payroll vs Non-Payroll: Full Dimension Comparison")
)

display(styled_comp)

# ---------------------------------------------------------------------------
# 3. Multiplier horizontal bar chart
# ---------------------------------------------------------------------------
# Exclude 'Account Count' from multiplier chart (not a per-member metric)
chart_df = comp_df[comp_df['Metric'] != 'Account Count'].copy()
chart_df = chart_df.sort_values('Multiplier', ascending=True)

if len(chart_df) > 0:
    fig, ax = plt.subplots(figsize=(14, max(7, len(chart_df) * 0.8)))

    colors = [GEN_COLORS['accent'] if m >= 1.5 else GEN_COLORS['info']
              for m in chart_df['Multiplier']]

    bars = ax.barh(range(len(chart_df)), chart_df['Multiplier'],
                   color=colors, edgecolor='white', linewidth=1.5, zorder=3)

    # Reference line at 1.0x
    ax.axvline(x=1.0, color=GEN_COLORS['muted'], linestyle='--',
               linewidth=2, alpha=0.7, zorder=2)
    ax.text(1.0, len(chart_df) - 0.3, '  1.0x (parity)',
            fontsize=11, color=GEN_COLORS['muted'], style='italic')

    # Value labels
    for i, (bar, mult) in enumerate(zip(bars, chart_df['Multiplier'])):
        ax.text(bar.get_width() + 0.05, bar.get_y() + bar.get_height() / 2,
                f"{mult:.2f}x", ha='left', va='center',
                fontsize=13, fontweight='bold', color=GEN_COLORS['dark_text'])

    ax.set_yticks(range(len(chart_df)))
    ax.set_yticklabels(chart_df['Metric'], fontsize=13, fontweight='bold')
    ax.set_xlabel('')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f"{x:.1f}x"))

    gen_clean_axes(ax, keep_bottom=True)

    ax.set_title("Payroll Member Value Multiplier",
                 fontsize=24, fontweight='bold', color=GEN_COLORS['dark_text'],
                 loc='left', pad=20)
    ax.text(0.0, 1.03,
            f"How much more valuable are payroll members?  --  {DATASET_LABEL}",
            fontsize=13, style='italic', color=GEN_COLORS['muted'],
            transform=ax.transAxes)

    plt.tight_layout()
    plt.show()

# Print top multiplier
if len(comp_df) > 1:
    top_mult = comp_df[comp_df['Metric'] != 'Account Count'].sort_values(
        'Multiplier', ascending=False
    ).iloc[0]
    print(f"\nHighest multiplier: {top_mult['Metric']} at {top_mult['Multiplier']:.2f}x")
