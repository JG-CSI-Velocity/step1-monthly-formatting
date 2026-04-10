# ===========================================================================
# SEGMENT DISTRIBUTION: Stacked Area Across Bimonthly Waves
# ===========================================================================
# Shows how segment composition shifts over 6 waves.
# X-axis = wave dates, stacked areas = segment proportions.

if 'seg_evo_df' not in dir() or len(seg_evo_df) == 0 or len(SEG_COLS) == 0:
    print("    No segment evolution data available. Skipping distribution chart.")
else:
    # ------------------------------------------------------------------
    # Build wave-by-wave distribution counts
    # ------------------------------------------------------------------
    wave_dist = []
    for col, wave_label in zip(SEG_COLS, SEG_WAVES):
        counts = (
            seg_evo_df[col]
            .astype(str).str.strip()
            .replace({'': np.nan, 'nan': np.nan})
            .dropna()
            .value_counts()
        )
        for seg_val in SEG_ORDER:
            wave_dist.append({
                'wave': wave_label,
                'segment': seg_val,
                'count': counts.get(seg_val, 0),
            })

    wave_dist_df = pd.DataFrame(wave_dist)

    # Pivot: rows = waves, columns = segments (ordered)
    pivot = wave_dist_df.pivot(index='wave', columns='segment', values='count')
    pivot = pivot.reindex(index=SEG_WAVES)
    pivot = pivot[SEG_ORDER].fillna(0)

    # Compute percentages for display
    pivot_pct = pivot.div(pivot.sum(axis=1), axis=0) * 100

    # ------------------------------------------------------------------
    # Stacked area chart
    # ------------------------------------------------------------------
    # Build a color palette for segments
    base_colors = [
        GEN_COLORS['info'], GEN_COLORS['success'], GEN_COLORS['warning'],
        GEN_COLORS['accent'], GEN_COLORS['primary'], GEN_COLORS['muted'],
    ]
    # Extend palette if more segments than colors
    seg_colors = []
    for i, seg in enumerate(SEG_ORDER):
        seg_colors.append(base_colors[i % len(base_colors)])

    fig, ax = plt.subplots(figsize=(16, 8))

    x = range(len(SEG_WAVES))
    ax.stackplot(
        x,
        [pivot_pct[seg].values for seg in SEG_ORDER],
        labels=SEG_ORDER,
        colors=seg_colors,
        alpha=0.85,
        edgecolor='white',
        linewidth=0.5,
    )

    ax.set_xticks(x)
    ax.set_xticklabels(SEG_WAVES, fontsize=14, fontweight='bold')
    ax.set_ylabel("% of Accounts", fontsize=16, fontweight='bold', labelpad=10)
    ax.set_ylim(0, 100)
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(gen_fmt_pct))

    gen_clean_axes(ax, keep_left=True, keep_bottom=True)
    ax.yaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
    ax.set_axisbelow(True)

    # Legend
    handles, labels = ax.get_legend_handles_labels()
    ax.legend(handles[::-1], labels[::-1],
              loc='upper left', bbox_to_anchor=(1.02, 1.0),
              fontsize=12, frameon=False, title='Segment',
              title_fontproperties={'weight': 'bold', 'size': 13})

    ax.set_title("Segment Composition Across Bimonthly Waves",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02,
            f"Which segments are growing or shrinking?  ({DATASET_LABEL})",
            transform=ax.transAxes, fontsize=15,
            color=GEN_COLORS['muted'], style='italic')

    # Annotate segment counts per wave along bottom
    for i, wave in enumerate(SEG_WAVES):
        total = int(pivot.iloc[i].sum())
        ax.text(i, -5, f"n={total:,}",
                ha='center', va='top', fontsize=10,
                color=GEN_COLORS['muted'], fontweight='bold')

    plt.tight_layout()
    plt.show()
