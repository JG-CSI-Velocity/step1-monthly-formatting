# ===========================================================================
# INTERCHANGE ACTION SUMMARY -- REVENUE OPPORTUNITY SIZING
# ===========================================================================
# Executive-level summary: how much money is on the table and what to do.

num_months = len(MONTH_LABELS)
annualization = 12.0 / num_months if num_months > 0 else 1.0

pin_total = interchange_df['total_pin_dollars'].sum()
sig_total = interchange_df['total_sig_dollars'].sum()
all_spend = pin_total + sig_total
current_ic = interchange_df['total_interchange'].sum()
current_ic_annual = current_ic * annualization
overall_sig_ratio = sig_total / max(1, all_spend) * 100

# -----------------------------------------------------------------------
# Scenario modeling
# -----------------------------------------------------------------------
def _scenario_ic(shift_pct):
    """Compute annualized IC if shift_pct of PIN migrates to SIG."""
    new_pin = pin_total * (1 - shift_pct)
    new_sig = sig_total + pin_total * shift_pct
    return (new_pin * PIN_RATE + new_sig * SIG_RATE) * annualization

ic_10 = _scenario_ic(0.10)
ic_25 = _scenario_ic(0.25)
ic_50 = _scenario_ic(0.50)
ic_max = all_spend * SIG_RATE * annualization

gain_10 = ic_10 - current_ic_annual
gain_25 = ic_25 - current_ic_annual
gain_50 = ic_50 - current_ic_annual
gain_max = ic_max - current_ic_annual

# -----------------------------------------------------------------------
# Top merchant targets (if merchant analysis ran)
# -----------------------------------------------------------------------
top_merchant_targets = []
try:
    if 'merchant_agg' in dir() and merchant_agg is not None and len(merchant_agg) > 0:
        opp_merchants = merchant_agg.nlargest(3, 'est_opportunity')
        for _, row in opp_merchants.iterrows():
            m_col = merchant_col if merchant_col else 'merchant'
            top_merchant_targets.append({
                'name': row.get(m_col, 'Unknown'),
                'sig_ratio': row.get('avg_sig_ratio', 0),
                'opportunity': row.get('est_opportunity', 0),
            })
except NameError:
    pass

# -----------------------------------------------------------------------
# Product-level recommendations
# -----------------------------------------------------------------------
product_recs = []
try:
    if prod_col and 'prod_agg' in dir() and prod_agg is not None:
        pin_defaults = prod_agg[prod_agg['sig_ratio'] < 40].nlargest(
            3, 'opportunity')
        for _, row in pin_defaults.iterrows():
            product_recs.append({
                'product': row[prod_col],
                'sig_ratio': row['sig_ratio'],
                'opportunity': row['opportunity'],
                'accounts': row['acct_count'],
            })
except NameError:
    pass

# -----------------------------------------------------------------------
# Visual summary card
# -----------------------------------------------------------------------
fig = plt.figure(figsize=(18, 10))
gs = GridSpec(3, 2, figure=fig, hspace=0.4, wspace=0.3)

# -- TOP ROW: Revenue Opportunity Scenarios ----------------------------
ax_scenarios = fig.add_subplot(gs[0, :])
ax_scenarios.set_axis_off()

scenarios = [
    ('Current', current_ic_annual, GEN_COLORS['muted']),
    ('10% Shift', ic_10, GEN_COLORS['info']),
    ('25% Shift', ic_25, GEN_COLORS['success']),
    ('50% Shift', ic_50, GEN_COLORS['warning']),
    ('Max (100%)', ic_max, GEN_COLORS['accent']),
]

card_width = 0.18
gap = 0.01
start_x = 0.02
for i, (label, val, color) in enumerate(scenarios):
    x0 = start_x + i * (card_width + gap)
    card = FancyBboxPatch(
        (x0, 0.05), card_width, 0.85,
        boxstyle="round,pad=0.03",
        facecolor=color, alpha=0.12,
        edgecolor=color, linewidth=2,
        transform=ax_scenarios.transAxes
    )
    ax_scenarios.add_patch(card)
    ax_scenarios.text(x0 + card_width / 2, 0.70, label,
                      fontsize=13, fontweight='bold', color=color,
                      ha='center', va='center',
                      transform=ax_scenarios.transAxes)
    ax_scenarios.text(x0 + card_width / 2, 0.40,
                      f"${val:,.0f}/yr",
                      fontsize=16, fontweight='bold', color=color,
                      ha='center', va='center',
                      transform=ax_scenarios.transAxes)
    if i > 0:
        delta = val - current_ic_annual
        ax_scenarios.text(x0 + card_width / 2, 0.15,
                          f"+${delta:,.0f}",
                          fontsize=11, fontstyle='italic',
                          color=GEN_COLORS['success'],
                          ha='center', va='center',
                          transform=ax_scenarios.transAxes)

# -- MIDDLE LEFT: Top Merchant Targets ---------------------------------
ax_merch = fig.add_subplot(gs[1, 0])
ax_merch.set_axis_off()
ax_merch.set_title("Top 3 Merchant Targets for PIN-to-SIG",
                    fontsize=16, fontweight='bold', loc='left',
                    color=GEN_COLORS['dark_text'])

if top_merchant_targets:
    for i, target in enumerate(top_merchant_targets):
        y = 0.75 - i * 0.28
        ax_merch.text(0.05, y,
                      f"{i+1}. {target['name']}",
                      fontsize=13, fontweight='bold',
                      color=GEN_COLORS['primary'],
                      transform=ax_merch.transAxes)
        ax_merch.text(0.05, y - 0.12,
                      f"   SIG Ratio: {target['sig_ratio']:.0%}  |  "
                      f"Opportunity: ${target['opportunity']:,.0f}",
                      fontsize=11, color=GEN_COLORS['muted'],
                      transform=ax_merch.transAxes)
else:
    ax_merch.text(0.05, 0.5,
                  "Run cell 08 for merchant-level targets",
                  fontsize=12, color=GEN_COLORS['muted'],
                  transform=ax_merch.transAxes, fontstyle='italic')

# -- MIDDLE RIGHT: Product Recommendations ----------------------------
ax_prod = fig.add_subplot(gs[1, 1])
ax_prod.set_axis_off()
ax_prod.set_title("Product-Level Recommendations",
                   fontsize=16, fontweight='bold', loc='left',
                   color=GEN_COLORS['dark_text'])

if product_recs:
    for i, rec in enumerate(product_recs):
        y = 0.75 - i * 0.28
        ax_prod.text(0.05, y,
                     f"{i+1}. {rec['product']}",
                     fontsize=13, fontweight='bold',
                     color=GEN_COLORS['accent'],
                     transform=ax_prod.transAxes)
        ax_prod.text(0.05, y - 0.12,
                     f"   SIG: {rec['sig_ratio']:.1f}%  |  "
                     f"{rec['accounts']:,} accts  |  "
                     f"Opp: ${rec['opportunity']:,.0f}",
                     fontsize=11, color=GEN_COLORS['muted'],
                     transform=ax_prod.transAxes)
else:
    ax_prod.text(0.05, 0.5,
                 "Run cell 09 for product-level recommendations",
                 fontsize=12, color=GEN_COLORS['muted'],
                 transform=ax_prod.transAxes, fontstyle='italic')

# -- BOTTOM ROW: Key Takeaways ----------------------------------------
ax_bottom = fig.add_subplot(gs[2, :])
ax_bottom.set_axis_off()
ax_bottom.set_title("Key Takeaways",
                     fontsize=16, fontweight='bold', loc='left',
                     color=GEN_COLORS['dark_text'])

takeaways = [
    f"Current SIG ratio: {overall_sig_ratio:.1f}% -- "
    f"{'above' if overall_sig_ratio >= 60 else 'below'} the 60% goal",

    f"A realistic 10-25% PIN migration = "
    f"${gain_10:,.0f} to ${gain_25:,.0f} additional annual interchange",

    f"Theoretical maximum opportunity: ${gain_max:,.0f}/yr "
    f"(if all transactions routed as signature)",

    "Action: Review card product defaults, educate members at "
    "high-PIN merchants, consider contactless card upgrades",
]

for i, text in enumerate(takeaways):
    y = 0.80 - i * 0.22
    ax_bottom.text(0.03, y, f">> {text}",
                   fontsize=12, color=GEN_COLORS['dark_text'],
                   transform=ax_bottom.transAxes,
                   fontweight='bold' if i == 1 else 'normal')

fig.suptitle("Interchange Revenue -- Action Summary",
             fontsize=26, fontweight='bold', x=0.02, ha='left',
             color=GEN_COLORS['dark_text'])
fig.text(0.02, 0.95,
         f"PIN rate {PIN_RATE:.2%}  |  SIG rate {SIG_RATE:.2%}  |  "
         f"{num_months} months annualized  |  {DATASET_LABEL}",
         fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
         ha='left')

plt.tight_layout(rect=[0, 0, 1, 0.93])
plt.show()

# -----------------------------------------------------------------------
# Print summary for notebook output
# -----------------------------------------------------------------------
print(f"\n{'='*70}")
print(f"INTERCHANGE REVENUE -- OPPORTUNITY SIZING")
print(f"{'='*70}")
print(f"  Dataset Period           : {DATASET_LABEL} ({num_months} months)")
print(f"  Total Accounts           : {len(interchange_df):,}")
print(f"  Current SIG Ratio        : {overall_sig_ratio:.1f}%")
print(f"  Current Annual IC (est.) : ${current_ic_annual:,.0f}")
print(f"")
print(f"  SCENARIO ANALYSIS:")
print(f"    10% PIN shift          : +${gain_10:,.0f}/yr  "
      f"(total ${ic_10:,.0f}/yr)")
print(f"    25% PIN shift          : +${gain_25:,.0f}/yr  "
      f"(total ${ic_25:,.0f}/yr)")
print(f"    50% PIN shift          : +${gain_50:,.0f}/yr  "
      f"(total ${ic_50:,.0f}/yr)")
print(f"    100% SIG (theoretical) : +${gain_max:,.0f}/yr  "
      f"(total ${ic_max:,.0f}/yr)")
print(f"")

if top_merchant_targets:
    print(f"  TOP 3 MERCHANT TARGETS:")
    for i, t in enumerate(top_merchant_targets):
        print(f"    {i+1}. {t['name']:<30s}  "
              f"SIG: {t['sig_ratio']:.0%}  Opp: ${t['opportunity']:,.0f}")

if product_recs:
    print(f"  PRODUCT RECOMMENDATIONS (default PIN routing suspected):")
    for i, r in enumerate(product_recs):
        print(f"    {i+1}. {r['product']:<30s}  "
              f"SIG: {r['sig_ratio']:.1f}%  "
              f"Accts: {r['accounts']:,}")

print(f"{'='*70}")
