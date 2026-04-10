# ===========================================================================
# BALANCE vs ACTIVITY: Quadrant Scatter (Conference Edition)
# ===========================================================================
# Avg Bal (x) vs total_spend (y), colored by balance band.
# Quadrant annotations for strategic segmentation.

fig, ax = plt.subplots(figsize=(14, 7))

# Filter to accounts with positive balance and activity data
scatter_df = balance_df[
    (balance_df['Avg Bal'] > 0) & (balance_df['total_spend'] > 0)
].copy()

# Sample to 5000 max for readability
MAX_SCATTER = 5000
if len(scatter_df) > MAX_SCATTER:
    scatter_df = scatter_df.sample(n=MAX_SCATTER, random_state=42)

# ---------------------------------------------------------------------------
# Scatter plot colored by balance band
# ---------------------------------------------------------------------------
for band in BALANCE_BAND_ORDER:
    subset = scatter_df[scatter_df['balance_band'] == band]
    if len(subset) == 0:
        continue
    ax.scatter(subset['Avg Bal'], subset['total_spend'],
               c=bal_band_palette.get(band, GEN_COLORS['muted']),
               label=band, alpha=0.5, s=25, edgecolors='none')

# ---------------------------------------------------------------------------
# Quadrant lines at median
# ---------------------------------------------------------------------------
med_bal = scatter_df['Avg Bal'].median()
med_spend = scatter_df['total_spend'].median()

ax.axvline(med_bal, color=GEN_COLORS['muted'], linestyle='--',
           linewidth=1.5, alpha=0.6)
ax.axhline(med_spend, color=GEN_COLORS['muted'], linestyle='--',
           linewidth=1.5, alpha=0.6)

# ---------------------------------------------------------------------------
# Quadrant labels
# ---------------------------------------------------------------------------
x_min, x_max = ax.get_xlim()
y_min, y_max = ax.get_ylim()

quadrant_labels = [
    {'x': 0.78, 'y': 0.92, 'text': 'High Balance + Active\n(Ideal Members)',
     'color': GEN_COLORS['success']},
    {'x': 0.15, 'y': 0.92, 'text': 'Low Balance + Active\n(Deepen Relationship)',
     'color': GEN_COLORS['warning']},
    {'x': 0.78, 'y': 0.08, 'text': 'Sleeping Giants\n(Cross-Sell Opportunity)',
     'color': GEN_COLORS['accent']},
    {'x': 0.15, 'y': 0.08, 'text': 'At Risk\n(Low Everything)',
     'color': GEN_COLORS['muted']},
]

for q in quadrant_labels:
    ax.text(q['x'], q['y'], q['text'],
            transform=ax.transAxes, fontsize=11, fontweight='bold',
            ha='center', va='center', color=q['color'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                      edgecolor=q['color'], alpha=0.85))

# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------
ax.set_xscale('log')
ax.set_yscale('log')
ax.xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))

ax.set_xlabel("Average Balance", fontsize=14)
ax.set_ylabel("Total Card Spend", fontsize=14)

ax.set_title("Balance vs Card Activity",
             fontsize=24, fontweight='bold', loc='left',
             color=GEN_COLORS['dark_text'], pad=20)
ax.text(0.0, 1.03,
        f"Each dot = 1 account (sampled to {len(scatter_df):,}) | {DATASET_LABEL}",
        transform=ax.transAxes, fontsize=12, style='italic',
        color=GEN_COLORS['muted'])

ax.legend(title='Balance Band', loc='center left',
          bbox_to_anchor=(1.02, 0.5), fontsize=11,
          title_fontsize=12)

gen_clean_axes(ax)

plt.tight_layout()
plt.show()

# Quadrant counts
high_bal_active = scatter_df[
    (scatter_df['Avg Bal'] >= med_bal) & (scatter_df['total_spend'] >= med_spend)
]
sleeping_giants = scatter_df[
    (scatter_df['Avg Bal'] >= med_bal) & (scatter_df['total_spend'] < med_spend)
]

print(f"\n    INSIGHT: {len(high_bal_active):,} 'Ideal Members' -- "
      f"high balance + high activity.")
print(f"    INSIGHT: {len(sleeping_giants):,} 'Sleeping Giants' -- "
      f"high balance, low card usage. Cross-sell opportunity.")
print(f"    Sleeping Giants hold ${sleeping_giants['Avg Bal'].sum():,.0f} in deposits.")
