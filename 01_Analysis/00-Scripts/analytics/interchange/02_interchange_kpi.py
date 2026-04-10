# ===========================================================================
# INTERCHANGE KPI CARDS
# ===========================================================================
# 4-card dashboard: Total IC, SIG Ratio, 10% Shift Revenue, Max Opportunity

num_months = len(MONTH_LABELS)
annualization = 12.0 / num_months if num_months > 0 else 1.0

# -----------------------------------------------------------------------
# Compute KPI values
# -----------------------------------------------------------------------
total_ic_annual = interchange_df['total_interchange'].sum() * annualization

overall_sig_ratio_val = (
    interchange_df['total_sig_dollars'].sum()
    / max(1, interchange_df['total_pin_dollars'].sum()
          + interchange_df['total_sig_dollars'].sum())
) * 100

# 10% of current PIN dollars shifted to SIG
pin_total = interchange_df['total_pin_dollars'].sum()
sig_total = interchange_df['total_sig_dollars'].sum()
current_ic = interchange_df['total_interchange'].sum()
shift_10_ic = (pin_total * 0.90 * PIN_RATE
               + pin_total * 0.10 * SIG_RATE
               + sig_total * SIG_RATE)
revenue_10_shift = (shift_10_ic - current_ic) * annualization

# Theoretical max: all spend at SIG rate
max_ic_annual = (pin_total + sig_total) * SIG_RATE * annualization
revenue_max = (max_ic_annual - total_ic_annual)

# -----------------------------------------------------------------------
# KPI card layout
# -----------------------------------------------------------------------
kpi_data = [
    ("Estimated Annual\nInterchange",
     f"${total_ic_annual:,.0f}",
     f"{num_months}-month data annualized",
     GEN_COLORS['primary']),
    ("Portfolio\nSIG Ratio",
     f"{overall_sig_ratio_val:.1f}%",
     "% of dollars routed as signature",
     GEN_COLORS['info']),
    ("Revenue Gain\n10% PIN Shift",
     f"+${revenue_10_shift:,.0f}/yr",
     "If 10% of PIN$ moved to SIG",
     GEN_COLORS['success']),
    ("Theoretical Max\nOpportunity",
     f"+${revenue_max:,.0f}/yr",
     "If ALL transactions were SIG",
     GEN_COLORS['warning']),
]

fig, axes = plt.subplots(1, 4, figsize=(20, 5))
fig.suptitle("Interchange Revenue Overview",
             fontsize=26, fontweight='bold', x=0.02, ha='left',
             color=GEN_COLORS['dark_text'])
fig.text(0.02, 0.90,
         f"Durbin-exempt estimate  |  {DATASET_LABEL}",
         fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
         ha='left')

for ax, (title, value, sub, color) in zip(axes, kpi_data):
    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_axis_off()

    # Card background
    card = FancyBboxPatch(
        (0.03, 0.05), 0.94, 0.90,
        boxstyle="round,pad=0.04",
        facecolor=color, alpha=0.10,
        edgecolor=color, linewidth=2
    )
    ax.add_patch(card)

    ax.text(0.50, 0.78, title,
            fontsize=14, fontweight='bold', color=GEN_COLORS['muted'],
            ha='center', va='center')
    ax.text(0.50, 0.45, value,
            fontsize=30, fontweight='bold', color=color,
            ha='center', va='center')
    ax.text(0.50, 0.15, sub,
            fontsize=11, color=GEN_COLORS['muted'],
            ha='center', va='center', fontstyle='italic')

plt.tight_layout(rect=[0, 0, 1, 0.85])
plt.show()
