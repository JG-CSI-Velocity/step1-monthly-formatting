# ===========================================================================
# BALANCE vs COMPETITOR ACTIVITY: Depositor Leakage (Conference Edition)
# ===========================================================================
# Scatter: Avg Bal vs competitor_spend_pct. Identify high-balance members
# who rely heavily on competitors for daily spending.

# ---------------------------------------------------------------------------
# Check for competitor data
# ---------------------------------------------------------------------------
has_comp_data = ('competitor_spend_pct' in balance_df.columns and
                 balance_df['competitor_spend_pct'].sum() > 0)

if has_comp_data:
    fig, ax = plt.subplots(figsize=(14, 7))

    # Filter to accounts with positive balance and some spend
    comp_scatter = balance_df[
        (balance_df['Avg Bal'] > 0) &
        (balance_df['total_spend'] > 0)
    ].copy()

    # Sample to 5000 max
    MAX_SCATTER_COMP = 5000
    if len(comp_scatter) > MAX_SCATTER_COMP:
        comp_scatter = comp_scatter.sample(n=MAX_SCATTER_COMP, random_state=42)

    # -------------------------------------------------------------------
    # Scatter plot
    # -------------------------------------------------------------------
    scatter = ax.scatter(
        comp_scatter['Avg Bal'],
        comp_scatter['competitor_spend_pct'],
        c=comp_scatter['competitor_spend_pct'],
        cmap='RdYlGn_r',
        alpha=0.5, s=30, edgecolors='none'
    )

    # Danger zone: high balance + high competitor usage
    HIGH_BAL_LINE = 10_000
    HIGH_COMP_LINE = 30

    ax.axvline(HIGH_BAL_LINE, color=GEN_COLORS['muted'], linestyle='--',
               linewidth=1.5, alpha=0.5)
    ax.axhline(HIGH_COMP_LINE, color=GEN_COLORS['muted'], linestyle='--',
               linewidth=1.5, alpha=0.5)

    # Annotate danger zone
    danger_zone = comp_scatter[
        (comp_scatter['Avg Bal'] >= HIGH_BAL_LINE) &
        (comp_scatter['competitor_spend_pct'] >= HIGH_COMP_LINE)
    ]

    ax.text(0.78, 0.92,
            f"DANGER ZONE\n{len(danger_zone):,} accounts\n"
            f"{gen_fmt_dollar(danger_zone['Avg Bal'].sum(), None)} in deposits",
            transform=ax.transAxes, fontsize=12, fontweight='bold',
            ha='center', va='center', color=GEN_COLORS['accent'],
            bbox=dict(boxstyle='round,pad=0.5', facecolor='#FDECEA',
                      edgecolor=GEN_COLORS['accent'], alpha=0.9))

    ax.text(0.20, 0.08,
            "Loyal Depositors\n(Low Competitor Use)",
            transform=ax.transAxes, fontsize=11, fontweight='bold',
            ha='center', va='center', color=GEN_COLORS['success'],
            bbox=dict(boxstyle='round,pad=0.4', facecolor='white',
                      edgecolor=GEN_COLORS['success'], alpha=0.85))

    # -------------------------------------------------------------------
    # Formatting
    # -------------------------------------------------------------------
    ax.set_xscale('log')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_dollar))
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_pct))

    ax.set_xlabel("Average Balance", fontsize=14)
    ax.set_ylabel("Competitor Spend %", fontsize=14)

    ax.set_title("Balance vs Competitor Activity",
                 fontsize=24, fontweight='bold', loc='left',
                 color=GEN_COLORS['dark_text'], pad=20)
    ax.text(0.0, 1.03,
            f"Your best depositors may be using competitors for daily spending | {DATASET_LABEL}",
            transform=ax.transAxes, fontsize=12, style='italic',
            color=GEN_COLORS['muted'])

    cbar = plt.colorbar(scatter, ax=ax, shrink=0.7, pad=0.02)
    cbar.set_label('Competitor Spend %', fontsize=12)

    gen_clean_axes(ax)

    plt.tight_layout()
    plt.show()

    # -------------------------------------------------------------------
    # Insights
    # -------------------------------------------------------------------
    high_bal_accts = comp_scatter[comp_scatter['Avg Bal'] >= HIGH_BAL_LINE]
    high_bal_high_comp = high_bal_accts[
        high_bal_accts['competitor_spend_pct'] >= HIGH_COMP_LINE
    ]
    leakage_pct = (len(high_bal_high_comp) / len(high_bal_accts) * 100
                   if len(high_bal_accts) > 0 else 0)

    print(f"\n    INSIGHT: {len(high_bal_high_comp):,} of {len(high_bal_accts):,} "
          f"high-balance accounts ({leakage_pct:.1f}%) have significant "
          f"competitor card activity.")
    print(f"    INSIGHT: These accounts hold "
          f"{gen_fmt_dollar(high_bal_high_comp['Avg Bal'].sum(), None)} "
          f"in deposits but send {high_bal_high_comp['competitor_spend_pct'].mean():.1f}% "
          f"of spend to competitors.")
    print(f"    INSIGHT: Your best depositors are using competitors for daily spending -- "
          f"card activation and rewards programs could recapture this spend.")

else:
    # -------------------------------------------------------------------
    # No competitor data: show informative placeholder
    # -------------------------------------------------------------------
    fig, ax = plt.subplots(figsize=(14, 7))

    ax.text(0.5, 0.55,
            "Competitor Spend Data Not Available",
            transform=ax.transAxes, ha='center', va='center',
            fontsize=22, fontweight='bold', color=GEN_COLORS['dark_text'])
    ax.text(0.5, 0.40,
            "Run the competition analysis notebook to tag competitor transactions\n"
            "and enable balance-vs-competitor cross-referencing.",
            transform=ax.transAxes, ha='center', va='center',
            fontsize=14, color=GEN_COLORS['muted'], style='italic')

    ax.set_title("Balance vs Competitor Activity",
                 fontsize=24, fontweight='bold', loc='left',
                 color=GEN_COLORS['dark_text'], pad=20)
    ax.text(0.0, 1.03, f"{DATASET_LABEL}",
            transform=ax.transAxes, fontsize=12, style='italic',
            color=GEN_COLORS['muted'])
    ax.axis('off')

    plt.tight_layout()
    plt.show()

    print(f"\n    INSIGHT: Competitor data not available. Run competition analysis "
          f"to enable this cross-reference.")
