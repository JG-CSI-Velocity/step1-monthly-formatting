# ===========================================================================
# OPT-IN MIGRATION: First-Month to Last-Month Status Transition Matrix
# ===========================================================================
# Heatmap showing how accounts moved between Reg E statuses over the full
# observation period. Cells sized by account count.

# ---------------------------------------------------------------------------
# Build transition matrix
# ---------------------------------------------------------------------------
_status_cats = ['Opted-In', 'Opted-Out', 'Not Applicable', 'Unknown']

# Filter to statuses that actually exist in the data
_existing_first = set(rege_df['first_status'].dropna().unique())
_existing_last = set(rege_df['current_status'].dropna().unique())
_active_statuses = [s for s in _status_cats if s in _existing_first or s in _existing_last]

if not _active_statuses:
    _active_statuses = _status_cats

_transition = pd.crosstab(
    rege_df['first_status'],
    rege_df['current_status'],
    margins=False
)

# Reindex to ensure consistent ordering
_transition = _transition.reindex(
    index=_active_statuses, columns=_active_statuses, fill_value=0
)

# Percentage matrix for annotations
_total_accts = _transition.values.sum()
_transition_pct = (_transition / _total_accts * 100) if _total_accts > 0 else _transition * 0

# ---------------------------------------------------------------------------
# Plot heatmap
# ---------------------------------------------------------------------------
fig, ax = plt.subplots(figsize=(14, 10))

# Custom colormap: white -> primary navy
_cmap = LinearSegmentedColormap.from_list(
    'rege_heat', ['#FFFFFF', GEN_COLORS['info'], GEN_COLORS['primary']]
)

sns.heatmap(
    _transition,
    annot=False,
    cmap=_cmap,
    linewidths=2,
    linecolor='white',
    square=True,
    cbar_kws={'label': 'Account Count', 'shrink': 0.8},
    ax=ax
)

# Custom annotations: count + percentage
for i, row_status in enumerate(_active_statuses):
    for j, col_status in enumerate(_active_statuses):
        count = _transition.iloc[i, j]
        pct = _transition_pct.iloc[i, j]
        if count > 0:
            _text_color = 'white' if count > (_transition.values.max() * 0.5) else GEN_COLORS['dark_text']
            ax.text(
                j + 0.5, i + 0.5,
                f"{count:,}\n({pct:.1f}%)",
                ha='center', va='center',
                fontsize=14, fontweight='bold',
                color=_text_color
            )
        else:
            ax.text(
                j + 0.5, i + 0.5, "--",
                ha='center', va='center',
                fontsize=12, color=GEN_COLORS['muted']
            )

# Highlight diagonal (no-change cells)
for i in range(len(_active_statuses)):
    rect = plt.Rectangle(
        (i, i), 1, 1,
        fill=False, edgecolor=GEN_COLORS['warning'],
        linewidth=3, linestyle='--'
    )
    ax.add_patch(rect)

ax.set_xlabel(f"Status as of {REGE_MONTHS[-1] if REGE_MONTHS else 'Latest'}",
              fontsize=16, fontweight='bold', labelpad=12)
ax.set_ylabel(f"Status as of {REGE_MONTHS[0] if REGE_MONTHS else 'Earliest'}",
              fontsize=16, fontweight='bold', labelpad=12)
ax.set_xticklabels(ax.get_xticklabels(), rotation=30, ha='right', fontsize=13)
ax.set_yticklabels(ax.get_yticklabels(), rotation=0, fontsize=13)

ax.set_title("Reg E Status Migration Matrix",
             fontsize=26, fontweight='bold', loc='left',
             color=GEN_COLORS['dark_text'], pad=20)
ax.text(0.0, 1.02,
        f"How did opt-in status change from first to last month? | {DATASET_LABEL}",
        transform=ax.transAxes, fontsize=14, color=GEN_COLORS['muted'],
        style='italic')

plt.tight_layout()
plt.show()

# ---------------------------------------------------------------------------
# Summary statistics
# ---------------------------------------------------------------------------
_stayed_in = _transition.loc['Opted-In', 'Opted-In'] if 'Opted-In' in _transition.index and 'Opted-In' in _transition.columns else 0
_stayed_out = _transition.loc['Opted-Out', 'Opted-Out'] if 'Opted-Out' in _transition.index and 'Opted-Out' in _transition.columns else 0
_new_in = _transition.loc[:, 'Opted-In'].sum() - _stayed_in if 'Opted-In' in _transition.columns else 0
_new_out = _transition.loc[:, 'Opted-Out'].sum() - _stayed_out if 'Opted-Out' in _transition.columns else 0

print(f"\n    INSIGHT: {_stayed_in:,} accounts stayed opted-in (diagonal)")
print(f"    INSIGHT: {_stayed_out:,} accounts stayed opted-out (diagonal)")
print(f"    INSIGHT: {_new_in:,} accounts newly moved TO opted-in")
print(f"    INSIGHT: {_new_out:,} accounts newly moved TO opted-out")
print(f"    NOTE: Dashed yellow border highlights no-change diagonal cells")
