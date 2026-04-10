# ===========================================================================
# INTERCHANGE REVENUE WATERFALL
# ===========================================================================
# Current PIN IC -> Current SIG IC -> +10% shift -> +25% shift -> Max

num_months = len(MONTH_LABELS)
annualization = 12.0 / num_months if num_months > 0 else 1.0

pin_total = interchange_df['total_pin_dollars'].sum()
sig_total = interchange_df['total_sig_dollars'].sum()
all_spend = pin_total + sig_total

# Current annualized interchange components
current_pin_ic = pin_total * PIN_RATE * annualization
current_sig_ic = sig_total * SIG_RATE * annualization
current_total  = current_pin_ic + current_sig_ic

# Scenario: shift 10% of PIN$ to SIG routing
shifted_10_pin = pin_total * 0.90
shifted_10_sig = sig_total + pin_total * 0.10
ic_after_10    = (shifted_10_pin * PIN_RATE + shifted_10_sig * SIG_RATE) * annualization
gain_10        = ic_after_10 - current_total

# Scenario: shift 25% of PIN$ to SIG routing
shifted_25_pin = pin_total * 0.75
shifted_25_sig = sig_total + pin_total * 0.25
ic_after_25    = (shifted_25_pin * PIN_RATE + shifted_25_sig * SIG_RATE) * annualization
gain_25        = ic_after_25 - ic_after_10

# Theoretical max: all at SIG rate
max_ic = all_spend * SIG_RATE * annualization
gain_max = max_ic - ic_after_25

# -----------------------------------------------------------------------
# Waterfall chart
# -----------------------------------------------------------------------
categories = [
    'Current\nPIN IC',
    'Current\nSIG IC',
    '+10% PIN\nShift',
    '+25% PIN\nShift',
    'Remaining\nGap to Max',
    'Theoretical\nMax',
]
values = [current_pin_ic, current_sig_ic, gain_10, gain_25, gain_max, 0]

# Compute cumulative positions for waterfall bars
cumulative = np.zeros(len(values))
bottoms    = np.zeros(len(values))
cumulative[0] = values[0]
for i in range(1, len(values) - 1):
    bottoms[i] = cumulative[i - 1]
    cumulative[i] = cumulative[i - 1] + values[i]

# Last bar is the total (starts from 0)
values[-1] = max_ic
bottoms[-1] = 0
cumulative[-1] = max_ic

# Colors
colors = [
    GEN_COLORS['info'],       # PIN IC (current, muted)
    GEN_COLORS['primary'],    # SIG IC (current)
    GEN_COLORS['success'],    # 10% gain
    GEN_COLORS['success'],    # 25% gain
    GEN_COLORS['warning'],    # remaining gap
    GEN_COLORS['primary'],    # total max
]

fig, ax = plt.subplots(figsize=(16, 7))

bars = ax.bar(categories, values, bottom=bottoms, color=colors,
              edgecolor='white', linewidth=1.5, width=0.6, alpha=0.90)

# Value labels on bars
for i, (bar, val) in enumerate(zip(bars, values)):
    y_pos = bottoms[i] + val / 2
    label = f"${val:,.0f}"
    ax.text(bar.get_x() + bar.get_width() / 2, y_pos,
            label, ha='center', va='center',
            fontsize=13, fontweight='bold', color='white',
            path_effects=[pe.withStroke(linewidth=3, foreground='black')])

# Connector lines between bars (waterfall effect)
for i in range(len(values) - 2):
    ax.plot(
        [i + 0.3, i + 0.7],
        [cumulative[i], cumulative[i]],
        color=GEN_COLORS['muted'], linewidth=1.2, linestyle='--'
    )

ax.set_ylabel('Annualized Interchange ($)', fontsize=16, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))
gen_clean_axes(ax)

# Title
fig.suptitle("Interchange Revenue Waterfall -- Opportunity Sizing",
             fontsize=24, fontweight='bold', x=0.02, ha='left',
             color=GEN_COLORS['dark_text'])
fig.text(0.02, 0.92,
         f"Annualized estimate  |  PIN rate {PIN_RATE:.2%}  |  "
         f"SIG rate {SIG_RATE:.2%}  |  {DATASET_LABEL}",
         fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
         ha='left')

plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.show()
