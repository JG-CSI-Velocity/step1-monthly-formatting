# ===========================================================================
# MIGRATION BY SEGMENT: Who's Moving Up/Down? (Conference Edition)
# ===========================================================================
# Separate bar charts: net migration rate by campaign status and age band.

if 'migration_tier_df' not in dir() or len(migration_tier_df) == 0:
    print("    No migration tier data available. Skipping segment analysis.")
else:
    _first_month = migration_tier_df.columns[0]
    _last_month = migration_tier_df.columns[-1]
    _tier_rank = {'Power': 0, 'Heavy': 1, 'Moderate': 2, 'Light': 3, 'Dormant': 4}

    _first_rank = migration_tier_df[_first_month].map(_tier_rank)
    _last_rank = migration_tier_df[_last_month].map(_tier_rank)
    _direction = pd.Series('Stable', index=migration_tier_df.index)
    _direction[_last_rank < _first_rank] = 'Upgraded'
    _direction[_last_rank > _first_rank] = 'Downgraded'

    def _plot_migration_by(segment_map, segment_name, order, palette, subtitle):
        _segment_vals = migration_tier_df.index.map(segment_map).fillna('Unknown')

        _rows = []
        for seg in order:
            _mask = _segment_vals == seg
            _seg_count = _mask.sum()
            if _seg_count == 0:
                continue
            _seg_dir = _direction[_mask]
            _upgraded = (_seg_dir == 'Upgraded').sum()
            _downgraded = (_seg_dir == 'Downgraded').sum()
            _net = _upgraded - _downgraded
            _rows.append({
                'segment': seg,
                'count': _seg_count,
                'upgraded': _upgraded,
                'downgraded': _downgraded,
                'net': _net,
                'net_rate': _net / _seg_count * 100,
            })

        if len(_rows) == 0:
            return

        _df = pd.DataFrame(_rows)

        fig, ax = plt.subplots(figsize=(14, 7))
        x = range(len(_df))
        colors = [GEN_COLORS['success'] if v >= 0 else GEN_COLORS['accent'] for v in _df['net_rate']]

        bars = ax.bar(x, _df['net_rate'], color=colors,
                      edgecolor='white', linewidth=0.5, width=0.5)

        for bar, (_, row) in zip(bars, _df.iterrows()):
            _y = row['net_rate']
            _offset = (abs(_y) * 0.1 + 0.5) * (1 if _y >= 0 else -1)
            ax.text(bar.get_x() + bar.get_width() / 2, _y + _offset,
                    f"{row['net_rate']:+.1f}%\n({row['net']:+,})",
                    ha='center', va='bottom' if _y >= 0 else 'top',
                    fontsize=10, fontweight='bold',
                    color=palette.get(row['segment'], GEN_COLORS['muted']))

        ax.axhline(0, color=GEN_COLORS['dark_text'], linewidth=1, alpha=0.3)

        ax.set_xticks(x)
        ax.set_xticklabels(_df['segment'], fontsize=13, fontweight='bold')
        ax.set_ylabel("Net Migration Rate %", fontsize=16, fontweight='bold', labelpad=10)
        ax.yaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_pct))

        gen_clean_axes(ax, keep_left=True, keep_bottom=True)
        ax.yaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)

        ax.set_title(f"Net Engagement Migration by {segment_name}",
                     fontsize=26, fontweight='bold',
                     color=GEN_COLORS['dark_text'], pad=35, loc='left')
        ax.text(0.0, 1.02, subtitle,
                transform=ax.transAxes, fontsize=13,
                color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.show()

    # Chart 1: By campaign status
    if 'camp_acct' in dir() and len(camp_acct) > 0:
        _camp_map = camp_acct.set_index('primary_account_num')['camp_status'].to_dict()
        _camp_palette = {
            'Responder': GEN_COLORS['success'],
            'Non-Responder': GEN_COLORS['warning'],
            'Never Mailed': GEN_COLORS['muted'],
        }
        _plot_migration_by(
            _camp_map, 'Campaign Status',
            ['Responder', 'Non-Responder', 'Never Mailed'], _camp_palette,
            f"Do campaign responders show more engagement improvement?  ({DATASET_LABEL})"
        )

    # Chart 2: By age band
    if 'Account Holder Age' in rewards_df.columns:
        acct_col = 'Acct Number' if 'Acct Number' in rewards_df.columns else ' Acct Number'
        _age_raw = pd.to_numeric(rewards_df['Account Holder Age'], errors='coerce')
        _age_bands = pd.cut(
            _age_raw, bins=[0, 25, 35, 45, 55, 65, 200],
            labels=['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
        )
        _age_map = dict(zip(
            rewards_df[acct_col].astype(str).str.strip(),
            _age_bands.astype(str)
        ))
        _plot_migration_by(
            _age_map, 'Age Band',
            AGE_ORDER, AGE_PALETTE,
            f"Which age groups are gaining or losing engagement?  ({DATASET_LABEL})"
        )
