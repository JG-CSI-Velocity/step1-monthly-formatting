# ===========================================================================
# MIGRATION MATRIX: First-Wave vs Last-Wave Segment Heatmap
# ===========================================================================
# Rows = first-wave segment, columns = last-wave segment.
# Diagonal = stable accounts. Off-diagonal = migration flows.
# Cell values = account count + percentage. Color intensity by count.

if 'seg_evo_df' not in dir() or len(seg_evo_df) == 0 or len(SEG_ORDER) == 0:
    print("    No segment evolution data available. Skipping migration matrix.")
else:
    # Filter to accounts with both first and last segment
    matrix_df = seg_evo_df.dropna(subset=['first_segment', 'last_segment']).copy()

    if len(matrix_df) == 0:
        print("    No accounts with both first and last segment. Skipping.")
    else:
        # Build cross-tabulation
        cross = pd.crosstab(
            matrix_df['first_segment'],
            matrix_df['last_segment'],
        )

        # Reindex to ensure all segments appear in order
        cross = cross.reindex(index=SEG_ORDER, columns=SEG_ORDER, fill_value=0)

        # Compute percentages for annotation
        total_in_matrix = cross.values.sum()
        cross_pct = cross / total_in_matrix * 100

        # ------------------------------------------------------------------
        # Heatmap
        # ------------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(14, 10))

        # Custom colormap: light to primary navy
        cmap = LinearSegmentedColormap.from_list(
            'seg_heat',
            ['#F8F9FA', GEN_COLORS['info'], GEN_COLORS['primary']],
            N=256
        )

        # Build annotation strings: count + pct
        annot_strings = np.empty_like(cross, dtype=object)
        for i in range(cross.shape[0]):
            for j in range(cross.shape[1]):
                ct = cross.iloc[i, j]
                pct = cross_pct.iloc[i, j]
                if ct > 0:
                    annot_strings[i, j] = f"{ct:,}\n({pct:.1f}%)"
                else:
                    annot_strings[i, j] = ""

        sns.heatmap(
            cross,
            ax=ax,
            annot=annot_strings,
            fmt='',
            cmap=cmap,
            linewidths=2,
            linecolor='white',
            cbar_kws={
                'label': 'Account Count',
                'shrink': 0.7,
            },
            square=True,
        )

        ax.set_xlabel("Last-Wave Segment", fontsize=16, fontweight='bold',
                       labelpad=12)
        ax.set_ylabel("First-Wave Segment", fontsize=16, fontweight='bold',
                       labelpad=12)
        ax.tick_params(axis='both', labelsize=13)

        # Highlight diagonal (stable) with subtle border
        for i in range(len(SEG_ORDER)):
            ax.add_patch(plt.Rectangle(
                (i, i), 1, 1,
                fill=False, edgecolor=GEN_COLORS['success'],
                linewidth=3, clip_on=False
            ))

        ax.set_title("Segment Migration Matrix: First Wave vs. Last Wave",
                     fontsize=26, fontweight='bold',
                     color=GEN_COLORS['dark_text'], pad=35, loc='left')
        ax.text(0.0, 1.03,
                f"Diagonal = stable accounts, off-diagonal = migration  ({DATASET_LABEL})",
                transform=ax.transAxes, fontsize=15,
                color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.show()

        # Print summary
        diag_total = sum(cross.iloc[i, i] for i in range(len(SEG_ORDER)))
        off_diag = total_in_matrix - diag_total
        print(f"\n    Migration matrix: {total_in_matrix:,} accounts")
        print(f"    Diagonal (stable): {diag_total:,} ({diag_total/total_in_matrix*100:.1f}%)")
        print(f"    Off-diagonal (migrated): {off_diag:,} ({off_diag/total_in_matrix*100:.1f}%)")
