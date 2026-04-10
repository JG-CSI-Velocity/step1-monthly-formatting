# ===========================================================================
# PIN-HEAVY ACCOUNTS -- CONVERSION OPPORTUNITIES
# ===========================================================================
# Accounts where >80% of transaction dollars are PIN-routed.
# These represent the largest single-account conversion opportunities.

# -----------------------------------------------------------------------
# Identify PIN-heavy accounts (>80% PIN by dollars)
# -----------------------------------------------------------------------
active = interchange_df[
    (interchange_df['total_pin_dollars'] + interchange_df['total_sig_dollars']) > 0
].copy()

active['pin_ratio'] = (
    active['total_pin_dollars']
    / (active['total_pin_dollars'] + active['total_sig_dollars'])
)

PIN_HEAVY_THRESHOLD = 0.80
pin_heavy = active[active['pin_ratio'] >= PIN_HEAVY_THRESHOLD].copy()

total_active = len(active)
total_pin_heavy = len(pin_heavy)
pin_heavy_pct = total_pin_heavy / max(1, total_active) * 100

print(f"PIN-Heavy Accounts (>={PIN_HEAVY_THRESHOLD:.0%} PIN by dollars):")
print(f"  {total_pin_heavy:,} of {total_active:,} active accounts "
      f"({pin_heavy_pct:.1f}%)")
print(f"  Combined opportunity: "
      f"${pin_heavy['opportunity'].sum():,.0f} over {len(MONTH_LABELS)} months")

# -----------------------------------------------------------------------
# Group by product type (if available)
# -----------------------------------------------------------------------
group_col = None
group_label = 'Product Type'
if 'Prod Desc' in pin_heavy.columns and pin_heavy['Prod Desc'].notna().sum() > 0:
    group_col = 'Prod Desc'
elif 'Prod Code' in pin_heavy.columns and pin_heavy['Prod Code'].notna().sum() > 0:
    group_col = 'Prod Code'
elif 'Business?' in pin_heavy.columns and pin_heavy['Business?'].notna().sum() > 0:
    group_col = 'Business?'
    group_label = 'Account Type'

if group_col is not None:
    grouped = (
        pin_heavy.groupby(group_col)
        .agg(
            count=('acct_number', 'count'),
            total_opp=('opportunity', 'sum'),
        )
        .sort_values('count', ascending=True)
        .tail(15)
    )
else:
    # Fallback: bucket by total spend amount
    spend = pin_heavy['total_pin_dollars'] + pin_heavy['total_sig_dollars']
    bins = [0, 500, 2000, 5000, 10000, 50000, float('inf')]
    bin_labels = ['<$500', '$500-2K', '$2K-5K', '$5K-10K', '$10K-50K', '$50K+']
    pin_heavy['spend_band'] = pd.cut(spend, bins=bins, labels=bin_labels, right=False)
    group_col = 'spend_band'
    group_label = 'Spend Band'
    grouped = (
        pin_heavy.groupby(group_col, observed=True)
        .agg(
            count=('acct_number', 'count'),
            total_opp=('opportunity', 'sum'),
        )
        .sort_values('count', ascending=True)
    )

# -----------------------------------------------------------------------
# Chart: Horizontal bar -- count of PIN-heavy accounts by group
# -----------------------------------------------------------------------
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(18, 7),
                                gridspec_kw={'width_ratios': [1, 1]})

# Panel 1: Count of PIN-heavy accounts
y_pos = np.arange(len(grouped))
bars1 = ax1.barh(y_pos, grouped['count'], color=GEN_COLORS['accent'],
                 alpha=0.85, height=0.6)
ax1.set_yticks(y_pos)
ax1.set_yticklabels(grouped.index, fontsize=12)
ax1.set_xlabel('Number of Accounts', fontsize=14, fontweight='bold')
ax1.set_title(f'PIN-Heavy Accounts\nby {group_label}',
              fontsize=18, fontweight='bold', loc='left')
ax1.xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_count))

for bar, val in zip(bars1, grouped['count']):
    ax1.text(bar.get_width() + max(grouped['count']) * 0.02,
             bar.get_y() + bar.get_height() / 2,
             f"{val:,}", va='center', fontsize=12, fontweight='bold',
             color=GEN_COLORS['dark_text'])
gen_clean_axes(ax1)

# Panel 2: Opportunity dollars by group
bars2 = ax2.barh(y_pos, grouped['total_opp'], color=GEN_COLORS['success'],
                 alpha=0.85, height=0.6)
ax2.set_yticks(y_pos)
ax2.set_yticklabels(grouped.index, fontsize=12)
ax2.set_xlabel('Interchange Opportunity ($)', fontsize=14, fontweight='bold')
ax2.set_title(f'Revenue Opportunity\nby {group_label}',
              fontsize=18, fontweight='bold', loc='left')
ax2.xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))

for bar, val in zip(bars2, grouped['total_opp']):
    ax2.text(bar.get_width() + max(grouped['total_opp']) * 0.02,
             bar.get_y() + bar.get_height() / 2,
             f"${val:,.0f}", va='center', fontsize=12, fontweight='bold',
             color=GEN_COLORS['dark_text'])
gen_clean_axes(ax2)

fig.suptitle(f"PIN-Heavy Accounts -- Conversion Opportunities "
             f"(>={PIN_HEAVY_THRESHOLD:.0%} PIN)",
             fontsize=24, fontweight='bold', x=0.02, ha='left',
             color=GEN_COLORS['dark_text'])
fig.text(0.02, 0.93,
         f"{total_pin_heavy:,} accounts  |  {DATASET_LABEL}",
         fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
         ha='left')

plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.show()
