# ===========================================================================
# PIN vs SIG DOLLAR TREND (DUAL AXIS)
# ===========================================================================
# Left axis: PIN$ and SIG$ monthly volumes
# Right axis: SIG ratio (% of dollars that are signature)

fig, ax1 = plt.subplots(figsize=(16, 7))

x = np.arange(len(monthly_interchange))
labels = monthly_interchange['month'].values

# Left axis -- dollar volumes as bars
bar_width = 0.35
bars_pin = ax1.bar(x - bar_width / 2,
                   monthly_interchange['pin_dollars'],
                   width=bar_width, label='PIN Dollars',
                   color=GEN_COLORS['accent'], alpha=0.85)
bars_sig = ax1.bar(x + bar_width / 2,
                   monthly_interchange['sig_dollars'],
                   width=bar_width, label='SIG Dollars',
                   color=GEN_COLORS['info'], alpha=0.85)

ax1.set_ylabel('Transaction Dollars', fontsize=16, fontweight='bold')
ax1.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))
ax1.set_xticks(x)
ax1.set_xticklabels(labels, rotation=45, ha='right', fontsize=12)
gen_clean_axes(ax1)

# Right axis -- SIG ratio line
ax2 = ax1.twinx()
sig_ratios = monthly_interchange['sig_ratio'].values * 100
ax2.plot(x, sig_ratios, color=GEN_COLORS['warning'],
         linewidth=3, marker='o', markersize=8, label='SIG Ratio %',
         zorder=5)
ax2.set_ylabel('SIG Ratio (%)', fontsize=16, fontweight='bold',
               color=GEN_COLORS['warning'])
ax2.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_pct))
ax2.set_ylim(0, 100)
ax2.spines['top'].set_visible(False)
ax2.spines['left'].set_visible(False)

# Annotate trend direction
if len(sig_ratios) >= 3:
    early_avg = np.mean(sig_ratios[:3])
    late_avg = np.mean(sig_ratios[-3:])
    delta = late_avg - early_avg
    direction = "IMPROVING" if delta > 1 else ("DECLINING" if delta < -1 else "STABLE")
    arrow = "^" if delta > 1 else ("v" if delta < -1 else "-")
    ax2.annotate(
        f"SIG Trend: {direction} ({delta:+.1f}pp)",
        xy=(x[-1], sig_ratios[-1]),
        xytext=(x[-1] - 2, sig_ratios[-1] + 8),
        fontsize=13, fontweight='bold',
        color=GEN_COLORS['success'] if delta > 0 else GEN_COLORS['accent'],
        arrowprops=dict(arrowstyle='->', lw=1.5,
                        color=GEN_COLORS['success'] if delta > 0
                        else GEN_COLORS['accent']),
    )

# Title
fig.suptitle("PIN vs Signature Dollar Volume & SIG Ratio Trend",
             fontsize=24, fontweight='bold', x=0.02, ha='left',
             color=GEN_COLORS['dark_text'])
fig.text(0.02, 0.92,
         f"Monthly transaction routing  |  {DATASET_LABEL}",
         fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
         ha='left')

# Combined legend
lines1, labels1 = ax1.get_legend_handles_labels()
lines2, labels2 = ax2.get_legend_handles_labels()
ax1.legend(lines1 + lines2, labels1 + labels2,
           loc='upper left', fontsize=13)

plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.show()
