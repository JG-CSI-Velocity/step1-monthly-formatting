# ===========================================================================
# NON-BANK THREATS: Payment Ecosystems Eroding Banking (Conference Edition)
# ===========================================================================
# These aren't competing banks -- they're replacing banking functions.
# Wallets, P2P, and BNPL handle payments, transfers, and credit that
# members used to do through their credit union.

if len(all_competitor_data) > 0:
    # Use derived config list (wallets, p2p, bnpl)
    _ecosystem_cats = PAYMENT_ECOSYSTEMS if 'PAYMENT_ECOSYSTEMS' in dir() else []

    total_accounts = combined_df['primary_account_num'].nunique()
    _n_months = DATASET_MONTHS if 'DATASET_MONTHS' in dir() else 1

    _nb_rows = []

    for competitor, comp_txns in all_competitor_data.items():
        category = comp_txns['competitor_category'].iloc[0]

        if category not in _ecosystem_cats:
            continue

        _nb_rows.append({
            'service': normalize_competitor_name(competitor),
            'category': category,
            'total_spend': comp_txns['amount'].sum(),
            'unique_accounts': comp_txns['primary_account_num'].nunique(),
            'transactions': len(comp_txns),
        })

    if len(_nb_rows) > 0:
        _nbdf = pd.DataFrame(_nb_rows)

        # Roll up normalized names. BUG FIX: accounts routinely use multiple
        # ecosystem services (Apple Pay + Venmo + PayPal + Cash App), so
        # summing per-variant unique_accounts over-counts severely. Rebuild
        # via nunique on the ecosystem txn subset keyed by normalized service.
        _eco_txns = competitor_txns[competitor_txns['competitor_category'].isin(_ecosystem_cats)]
        _nbdf_accts = (
            _eco_txns.assign(
                _svc=_eco_txns['competitor_match'].apply(normalize_competitor_name)
            )
            .groupby('_svc')['primary_account_num'].nunique()
            .rename('unique_accounts')
            .reset_index()
            .rename(columns={'_svc': 'service'})
        )
        _nbdf = (
            _nbdf.groupby(['service', 'category'], as_index=False)
            .agg(
                total_spend=('total_spend', 'sum'),
                transactions=('transactions', 'sum'),
            )
            .merge(_nbdf_accts, on='service', how='left')
        )
        _nbdf['unique_accounts'] = _nbdf['unique_accounts'].fillna(0).astype(int)

        _nbdf['penetration_pct'] = _nbdf['unique_accounts'] / total_accounts * 100
        _nbdf['spend_per_mo'] = _nbdf['total_spend'] / _n_months
        _nbdf['category_label'] = _nbdf['category'].apply(clean_category)

        _plot = _nbdf.sort_values('unique_accounts', ascending=True)

        _bar_colors = [get_cat_color(cl) for cl in _plot['category_label']]

        _plot['short_name'] = _plot['service'].apply(
            lambda n: n[:25] + '..' if len(str(n)) > 27 else n
        )

        # ----- Chart: Non-bank services by member penetration -----
        fig, ax = plt.subplots(figsize=(14, max(7, len(_plot) * 0.55)))

        ax.barh(
            range(len(_plot)),
            _plot['unique_accounts'],
            color=_bar_colors,
            edgecolor='white',
            linewidth=1.5,
            height=0.6,
            zorder=3,
        )

        for i, (_, row) in enumerate(_plot.iterrows()):
            ax.text(
                row['unique_accounts'] * 1.02, i,
                f"{row['unique_accounts']:,} accts ({row['penetration_pct']:.1f}%)  |  "
                f"${row['total_spend']:,.0f}  |  ${row['spend_per_mo']:,.0f}/mo",
                fontsize=11, fontweight='bold',
                color=GEN_COLORS['dark_text'], va='center',
            )

        ax.set_yticks(range(len(_plot)))
        ax.set_yticklabels(_plot['short_name'], fontsize=12, fontweight='bold')
        ax.set_xlabel('Unique Members', fontsize=16, fontweight='bold', labelpad=12)
        ax.xaxis.set_major_formatter(plt.FuncFormatter(gen_fmt_count))

        gen_clean_axes(ax, keep_left=True, keep_bottom=True)
        ax.xaxis.grid(True, color=GEN_COLORS['grid'], linewidth=0.5, alpha=0.5)
        ax.set_axisbelow(True)
        ax.set_xlim(0, _plot['unique_accounts'].max() * 1.65)

        # Legend
        _legend_cats = _plot['category_label'].unique()
        _handles = [
            plt.Rectangle((0, 0), 1, 1, fc=get_cat_color(c), edgecolor='white', label=c)
            for c in _legend_cats
        ]
        ax.legend(handles=_handles, loc='lower right', fontsize=12, frameon=False)

        _ds_label = DATASET_LABEL if 'DATASET_LABEL' in dir() else ''
        ax.set_title(
            'Non-Bank Threats to Banking Relationship',
            fontsize=26, fontweight='bold',
            color=GEN_COLORS['dark_text'], pad=20, loc='left',
        )
        ax.text(
            0.0, 0.97,
            f"Services replacing traditional banking functions  |  {_ds_label}",
            transform=ax.transAxes, fontsize=14,
            color=GEN_COLORS['muted'], style='italic',
        )

        plt.tight_layout()
        plt.show()

        # ----- Category-level summary -----
        # BUG FIX: category-level accounts also can't be a sum across services
        # — many accounts use multiple wallets/P2P/BNPL. Compute via nunique
        # on the ecosystem txn subset keyed by category.
        _cat_accts = (
            _eco_txns.groupby('competitor_category')['primary_account_num']
            .nunique()
            .rename('accounts')
        )
        # Map raw category → display label the same way _nbdf did via clean_category
        _cat_accts.index = _cat_accts.index.map(clean_category)

        _cat_summary = (
            _nbdf.groupby('category_label')
            .agg(
                services=('service', 'nunique'),
                total_spend=('total_spend', 'sum'),
                spend_per_mo=('spend_per_mo', 'sum'),
            )
            .join(_cat_accts, how='left')
            .sort_values('accounts', ascending=False)
        )
        _cat_summary['accounts'] = _cat_summary['accounts'].fillna(0).astype(int)

        print(f"\n    NON-BANK ECOSYSTEM SUMMARY ({_ds_label}):")
        for cat_label, row in _cat_summary.iterrows():
            pen = row['accounts'] / total_accounts * 100
            print(f"      {cat_label:12s}  {row['services']:>2} services  "
                  f"{row['accounts']:>6,} members ({pen:.1f}%)  "
                  f"${row['total_spend']:>12,.0f} total  "
                  f"${row['spend_per_mo']:>10,.0f}/mo")

        # BUG FIX: grand total must be distinct-count across ALL ecosystem
        # services, not sum of per-service counts.
        _total_nb_accts = int(_eco_txns['primary_account_num'].nunique())
        _total_nb_spend = float(_nbdf['total_spend'].sum())
        print(f"\n    Combined non-bank footprint: {_total_nb_accts:,} member-relationships, "
              f"${_total_nb_spend:,.0f} total spend.")
        print("    These services handle payments, transfers, and credit traditionally done by banks.")
    else:
        print("No payment ecosystem data found (wallets, P2P, BNPL)")
