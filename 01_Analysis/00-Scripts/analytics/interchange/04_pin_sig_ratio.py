# ===========================================================================
# SIG RATIO TREND WITH COLOR ZONES
# ===========================================================================
# Single line: SIG/(PIN+SIG) over 17 months
# Green zone: >60% SIG | Yellow: 40-60% | Red: <40%

fig, ax = plt.subplots(figsize=(16, 7))

x = np.arange(len(monthly_interchange))
labels = monthly_interchange['month'].values
sig_pct = monthly_interchange['sig_ratio'].values * 100

# Color zones (background fills)
ax.axhspan(60, 100, color=GEN_COLORS['success'], alpha=0.08, label='Goal: >60% SIG')
ax.axhspan(40, 60,  color=GEN_COLORS['warning'], alpha=0.08, label='Caution: 40-60%')
ax.axhspan(0,  40,  color=GEN_COLORS['accent'],  alpha=0.08, label='Risk: <40% SIG')

# Horizontal reference lines
ax.axhline(60, color=GEN_COLORS['success'], linewidth=1, linestyle='--', alpha=0.5)
ax.axhline(40, color=GEN_COLORS['accent'],  linewidth=1, linestyle='--', alpha=0.5)

# SIG ratio line
ax.plot(x, sig_pct, color=GEN_COLORS['primary'], linewidth=3,
        marker='o', markersize=9, markerfacecolor='white',
        markeredgecolor=GEN_COLORS['primary'], markeredgewidth=2.5,
        zorder=5)

# Value labels on each point
for i, val in enumerate(sig_pct):
    ax.text(i, val + 2.0, f"{val:.1f}%",
            ha='center', va='bottom', fontsize=15, fontweight='bold',
            color=GEN_COLORS['primary'])

# Trend line (linear regression)
if len(x) >= 3:
    z = np.polyfit(x, sig_pct, 1)
    p = np.poly1d(z)
    ax.plot(x, p(x), color=GEN_COLORS['muted'], linewidth=2,
            linestyle=':', alpha=0.7, label=f"Trend ({z[0]:+.2f}pp/mo)")

# Formatting
ax.set_xticks(x)
ax.set_xticklabels(labels, rotation=45, ha='right', fontsize=14)
ax.set_ylim(0, 100)
ax.set_ylabel('SIG Ratio (%)', fontsize=16, fontweight='bold')
ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_pct))
gen_clean_axes(ax)

ax.legend(loc='lower right', fontsize=14)

# Title
fig.suptitle("Signature Routing Ratio -- Monthly Trend",
             fontsize=24, fontweight='bold', x=0.02, ha='left',
             color=GEN_COLORS['dark_text'])
fig.text(0.02, 0.92,
         f"SIG$ / (PIN$ + SIG$)  |  {DATASET_LABEL}",
         fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
         ha='left')

plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.show()
