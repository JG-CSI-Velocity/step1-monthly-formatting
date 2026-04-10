# ===========================================================================
# ENGAGEMENT MIGRATION MATRIX: Tier-to-Tier Heatmap (Conference Edition)
# ===========================================================================
# Heatmap: starting tier (rows) vs ending tier (columns).
# Diagonal = stable, above = upgraded, below = downgraded. (14,8).

if 'migration_matrix' not in dir() or not isinstance(migration_matrix, pd.DataFrame) or len(migration_matrix) == 0:
    print("    No migration matrix available. Skipping heatmap.")
else:
    fig, ax = plt.subplots(figsize=(14, 8))

    # Normalize to percentages (row-wise: % of starting tier that ended in each tier)
    _row_sums = migration_matrix.sum(axis=1)
    _pct_matrix = migration_matrix.div(_row_sums, axis=0) * 100
    _pct_matrix = _pct_matrix.fillna(0)

    # Custom colormap: white -> teal for diagonal/upgrades
    cmap = LinearSegmentedColormap.from_list(
        'migration', ['#FFFFFF', '#E9ECEF', GEN_COLORS['info'], GEN_COLORS['primary']]
    )

    sns.heatmap(
        _pct_matrix, annot=True, fmt='.0f', cmap=cmap,
        linewidths=2, linecolor='white',
        cbar_kws={'shrink': 0.6, 'label': '% of Starting Tier'},
        annot_kws={'fontsize': 14, 'fontweight': 'bold'},
        vmin=0, vmax=100,
        ax=ax
    )

    # Add raw counts as secondary annotation
    for i in range(len(migration_matrix)):
        for j in range(len(migration_matrix.columns)):
            _val = migration_matrix.iloc[i, j]
            if _val > 0:
                ax.text(j + 0.5, i + 0.75,
                        f"({_val:,})",
                        ha='center', va='center', fontsize=8,
                        color=GEN_COLORS['muted'])

    ax.set_xlabel(f'Ending Tier ({_month_labels[-1]})', fontsize=14, fontweight='bold', labelpad=10)
    ax.set_ylabel(f'Starting Tier ({_month_labels[0]})', fontsize=14, fontweight='bold', labelpad=10)
    ax.set_xticklabels(ax.get_xticklabels(), fontsize=12, fontweight='bold', rotation=0)
    ax.set_yticklabels(ax.get_yticklabels(), fontsize=12, fontweight='bold', rotation=0)

    ax.set_title("Engagement Tier Migration Matrix",
                 fontsize=26, fontweight='bold',
                 color=GEN_COLORS['dark_text'], pad=35, loc='left')
    ax.text(0.0, 1.02,
            f"Diagonal = stable  |  Left of diagonal = upgraded  |  Right = downgraded  ({DATASET_LABEL})",
            transform=ax.transAxes, fontsize=13,
            color=GEN_COLORS['muted'], style='italic')

    plt.tight_layout()
    plt.show()
