# ===========================================================================
# SEGMENT PREDICTION: Watch List for Degradation Risk
# ===========================================================================
# For accounts currently in the bottom 2 segments: predict who is most
# likely to degrade further based on trend, balance, and activity.
# Output: styled table of high-risk accounts.

if 'seg_evo_df' not in dir() or len(seg_evo_df) == 0 or len(SEG_ORDER) < 2:
    print("    Insufficient segment data for prediction analysis. Skipping.")
else:
    # ------------------------------------------------------------------
    # 1. Identify bottom 2 segments
    # ------------------------------------------------------------------
    bottom_segments = SEG_ORDER[:2]
    print(f"    Bottom 2 segments (by rank): {bottom_segments}")

    bottom_df = seg_evo_df[
        seg_evo_df['last_segment'].isin(bottom_segments)
    ].copy()

    if len(bottom_df) == 0:
        print("    No accounts currently in bottom segments. Skipping.")
    else:
        # ------------------------------------------------------------------
        # 2. Compute degradation risk score (0-100)
        # ------------------------------------------------------------------

        # Factor 1: Trend over waves (consistently declining?)
        def _compute_trend_score(row):
            """Score 0-100 based on how consistently rank has declined."""
            ranks = []
            for col in SEG_COLS:
                val = row.get(col)
                if pd.notna(val) and str(val).strip() in SEG_RANK:
                    ranks.append(SEG_RANK[str(val).strip()])
            if len(ranks) < 2:
                return 50  # neutral if insufficient data
            # Count consecutive declines
            declines = sum(
                1 for i in range(1, len(ranks)) if ranks[i] < ranks[i - 1]
            )
            decline_ratio = declines / (len(ranks) - 1)
            return decline_ratio * 100

        bottom_df['trend_score'] = bottom_df.apply(_compute_trend_score, axis=1)

        # Factor 2: Balance trend (Avg vs Curr -- declining balance = risk)
        if 'Avg Bal' in bottom_df.columns and 'Curr Bal' in bottom_df.columns:
            bottom_df['bal_delta'] = bottom_df['Curr Bal'] - bottom_df['Avg Bal']
            # Normalize: accounts losing balance get higher risk
            bal_min = bottom_df['bal_delta'].min()
            bal_max = bottom_df['bal_delta'].max()
            bal_range = bal_max - bal_min if bal_max != bal_min else 1
            # Invert: lower delta = higher risk
            bottom_df['bal_risk_score'] = (
                (1 - (bottom_df['bal_delta'] - bal_min) / bal_range) * 100
            )
        else:
            bottom_df['bal_risk_score'] = 50
            bottom_df['bal_delta'] = np.nan

        # Factor 3: Data completeness (fewer waves = risk of disengagement)
        max_waves = len(SEG_COLS)
        bottom_df['completeness_risk'] = (
            (1 - bottom_df['waves_present'] / max_waves) * 100
        )

        # Composite risk score (weighted average)
        WEIGHT_TREND = 0.50
        WEIGHT_BALANCE = 0.30
        WEIGHT_COMPLETENESS = 0.20

        bottom_df['risk_score'] = (
            bottom_df['trend_score'] * WEIGHT_TREND
            + bottom_df['bal_risk_score'] * WEIGHT_BALANCE
            + bottom_df['completeness_risk'] * WEIGHT_COMPLETENESS
        ).round(1)

        # ------------------------------------------------------------------
        # 3. Flag watch list (top quartile of risk)
        # ------------------------------------------------------------------
        risk_threshold = bottom_df['risk_score'].quantile(0.75)
        watch_list = bottom_df[
            bottom_df['risk_score'] >= risk_threshold
        ].sort_values('risk_score', ascending=False)

        print(f"    Accounts in bottom segments: {len(bottom_df):,}")
        print(f"    Risk threshold (75th pctile): {risk_threshold:.1f}")
        print(f"    Watch list (high risk): {len(watch_list):,} accounts")

        # ------------------------------------------------------------------
        # 4. Display styled watch list table (top 30)
        # ------------------------------------------------------------------
        display_cols = ['Acct Number', 'last_segment', 'waves_present',
                        'risk_score', 'trend_score']
        optional_display = ['Avg Bal', 'Curr Bal', 'bal_delta',
                            'Account Holder Age', 'Prod Desc']
        for oc in optional_display:
            if oc in watch_list.columns:
                display_cols.append(oc)

        table_df = watch_list[display_cols].head(30).copy()

        # Rename for display
        rename_map = {
            'Acct Number': 'Account',
            'last_segment': 'Current Segment',
            'waves_present': 'Waves',
            'risk_score': 'Risk Score',
            'trend_score': 'Trend Risk',
            'Avg Bal': 'Avg Balance',
            'Curr Bal': 'Curr Balance',
            'bal_delta': 'Balance Change',
            'Account Holder Age': 'Age',
            'Prod Desc': 'Product',
        }
        table_df = table_df.rename(columns=rename_map)

        # Format dictionary
        fmt_dict = {'Risk Score': '{:.1f}', 'Trend Risk': '{:.0f}'}
        if 'Avg Balance' in table_df.columns:
            fmt_dict['Avg Balance'] = '${:,.0f}'
        if 'Curr Balance' in table_df.columns:
            fmt_dict['Curr Balance'] = '${:,.0f}'
        if 'Balance Change' in table_df.columns:
            fmt_dict['Balance Change'] = '${:,.0f}'
        if 'Age' in table_df.columns:
            fmt_dict['Age'] = '{:.0f}'

        styled = (
            table_df.style
            .hide(axis='index')
            .format(fmt_dict, na_rep='--')
            .background_gradient(
                subset=['Risk Score'],
                cmap='YlOrRd',
                vmin=0, vmax=100,
            )
            .set_properties(**{
                'font-size': '12px', 'font-weight': 'bold',
                'text-align': 'center', 'border': '1px solid #E9ECEF',
                'padding': '6px 10px',
            })
            .set_table_styles([
                {'selector': 'th', 'props': [
                    ('background-color', GEN_COLORS['accent']),
                    ('color', 'white'), ('font-size', '13px'),
                    ('font-weight', 'bold'), ('text-align', 'center'),
                    ('padding', '8px 10px'),
                ]},
                {'selector': 'caption', 'props': [
                    ('font-size', '22px'), ('font-weight', 'bold'),
                    ('color', GEN_COLORS['dark_text']),
                    ('text-align', 'left'),
                    ('padding-bottom', '12px'),
                ]},
            ])
            .set_caption(
                f"Degradation Watch List -- Accounts at Risk  ({DATASET_LABEL})"
            )
        )
        display(styled)

        # ------------------------------------------------------------------
        # 5. Risk score distribution chart
        # ------------------------------------------------------------------
        fig, ax = plt.subplots(figsize=(14, 7))

        bins = np.arange(0, 105, 10)
        ax.hist(bottom_df['risk_score'], bins=bins,
                color=GEN_COLORS['warning'], edgecolor='white',
                linewidth=0.5, alpha=0.85)

        # Mark threshold
        ax.axvline(x=risk_threshold, color=GEN_COLORS['accent'],
                   linewidth=2, linestyle='--', alpha=0.8)
        ax.text(risk_threshold + 1, ax.get_ylim()[1] * 0.9,
                f"Watch List\nThreshold: {risk_threshold:.0f}",
                fontsize=12, fontweight='bold',
                color=GEN_COLORS['accent'], va='top')

        ax.set_xlabel("Risk Score", fontsize=16, fontweight='bold',
                       labelpad=10)
        ax.set_ylabel("Number of Accounts", fontsize=16, fontweight='bold',
                       labelpad=10)
        ax.yaxis.set_major_formatter(
            mticker.FuncFormatter(gen_fmt_count)
        )

        gen_clean_axes(ax, keep_left=True, keep_bottom=True)
        ax.yaxis.grid(True, color=GEN_COLORS['grid'],
                      linewidth=0.5, alpha=0.7)
        ax.set_axisbelow(True)

        ax.set_title(
            "Risk Score Distribution: Bottom-Segment Accounts",
            fontsize=26, fontweight='bold',
            color=GEN_COLORS['dark_text'], pad=35, loc='left'
        )
        ax.text(0.0, 1.02,
                f"Who in the lowest segments is most likely to degrade further?  "
                f"({DATASET_LABEL})",
                transform=ax.transAxes, fontsize=15,
                color=GEN_COLORS['muted'], style='italic')

        plt.tight_layout()
        plt.show()
