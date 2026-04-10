# ===========================================================================
# SEGMENT EVOLUTION DATA: Bimonthly Segmentation Migration Pipeline
# ===========================================================================
# Auto-discovers segmentation columns from rewards_df, builds seg_evo_df
# with per-account migration tracking: first/last segment, direction,
# upgrade/degrade classification, demographic merge.
# Guard: gracefully handles missing or sparse segmentation data.

import re

try:
    # ------------------------------------------------------------------
    # 1. Auto-discover segmentation columns (pattern: MmmYY Segmentation)
    # ------------------------------------------------------------------
    rewards_cols = [c.strip() for c in rewards_df.columns]
    seg_pattern = re.compile(r'^[A-Z][a-z]{2}\d{2} Segmentation$')
    seg_cols_all = sorted(
        [c for c in rewards_cols if seg_pattern.match(c)],
        key=lambda c: pd.to_datetime(c.replace(' Segmentation', ''), format='%b%y')
    )

    if len(seg_cols_all) == 0:
        print("    No segmentation columns found in rewards_df. Skipping segment evolution.")
        seg_evo_df = pd.DataFrame()
        SEG_COLS = []
        SEG_WAVES = []
        SEG_ORDER = []
        SEG_RANK = {}
    else:
        SEG_COLS = seg_cols_all
        SEG_WAVES = [c.replace(' Segmentation', '') for c in SEG_COLS]
        n_waves = len(SEG_COLS)
        limited_data = n_waves < 3

        if limited_data:
            print(f"    NOTE: Only {n_waves} segmentation wave(s) found. "
                  "Migration analysis may be limited.")

        # ------------------------------------------------------------------
        # 2. Extract segmentation columns into wide format per account
        # ------------------------------------------------------------------
        id_col = 'Acct Number'
        keep_cols = [id_col] + SEG_COLS

        # Optional demographic/balance columns
        demo_candidates = [
            'Account Holder Age', 'Avg Bal', 'Curr Bal',
            'Prod Code', 'Prod Desc', 'Business?'
        ]
        demo_cols = [c for c in demo_candidates if c in rewards_cols]
        keep_cols += demo_cols

        seg_evo_df = rewards_df[keep_cols].copy()
        seg_evo_df[id_col] = seg_evo_df[id_col].astype(str).str.strip()

        # ------------------------------------------------------------------
        # 3. Discover unique segment values and build rank ordering
        # ------------------------------------------------------------------
        all_seg_values = set()
        for col in SEG_COLS:
            vals = seg_evo_df[col].dropna().unique()
            all_seg_values.update(vals)

        # Clean and sort segment values
        all_seg_values = sorted([str(v).strip() for v in all_seg_values if str(v).strip()])

        # Build numeric ranking: attempt to infer ordering.
        # Strategy: segments with higher average balance likely represent
        # higher-value tiers. Fall back to alphabetical if balance unavailable.
        if 'Avg Bal' in seg_evo_df.columns and len(all_seg_values) > 1:
            seg_avg_bal = {}
            for seg_val in all_seg_values:
                mask = pd.Series(False, index=seg_evo_df.index)
                for col in SEG_COLS:
                    mask |= (seg_evo_df[col].astype(str).str.strip() == seg_val)
                avg = pd.to_numeric(
                    seg_evo_df.loc[mask, 'Avg Bal'], errors='coerce'
                ).mean()
                seg_avg_bal[seg_val] = avg if pd.notna(avg) else 0

            # Rank: higher avg balance = higher rank
            SEG_ORDER = sorted(all_seg_values, key=lambda s: seg_avg_bal.get(s, 0))
        else:
            # Alphabetical fallback
            SEG_ORDER = sorted(all_seg_values)

        SEG_RANK = {seg: rank for rank, seg in enumerate(SEG_ORDER)}

        # ------------------------------------------------------------------
        # 4. Per-account: first_segment, last_segment, changed, direction
        # ------------------------------------------------------------------
        def _get_first_last(row):
            """Return first non-null and last non-null segment for an account."""
            vals = [row[c] for c in SEG_COLS if pd.notna(row[c]) and str(row[c]).strip()]
            if len(vals) == 0:
                return pd.Series({'first_segment': None, 'last_segment': None,
                                  'waves_present': 0})
            return pd.Series({
                'first_segment': str(vals[0]).strip(),
                'last_segment': str(vals[-1]).strip(),
                'waves_present': len(vals),
            })

        acct_seg_info = seg_evo_df.apply(_get_first_last, axis=1)
        seg_evo_df = pd.concat([seg_evo_df, acct_seg_info], axis=1)

        # Changed flag
        seg_evo_df['changed'] = (
            seg_evo_df['first_segment'] != seg_evo_df['last_segment']
        )

        # Direction: upgraded / degraded / stable
        def _direction(row):
            f_seg = row['first_segment']
            l_seg = row['last_segment']
            if pd.isna(f_seg) or pd.isna(l_seg):
                return 'unknown'
            f_rank = SEG_RANK.get(str(f_seg).strip(), -1)
            l_rank = SEG_RANK.get(str(l_seg).strip(), -1)
            if l_rank > f_rank:
                return 'upgraded'
            elif l_rank < f_rank:
                return 'degraded'
            return 'stable'

        seg_evo_df['direction'] = seg_evo_df.apply(_direction, axis=1)

        # ------------------------------------------------------------------
        # 5. Numeric balance columns
        # ------------------------------------------------------------------
        for bc in ['Avg Bal', 'Curr Bal']:
            if bc in seg_evo_df.columns:
                seg_evo_df[bc] = pd.to_numeric(seg_evo_df[bc], errors='coerce')

        if 'Account Holder Age' in seg_evo_df.columns:
            seg_evo_df['Account Holder Age'] = pd.to_numeric(
                seg_evo_df['Account Holder Age'], errors='coerce'
            )

        # ------------------------------------------------------------------
        # 6. Print summary
        # ------------------------------------------------------------------
        total_accts = len(seg_evo_df)
        with_data = (seg_evo_df['waves_present'] > 0).sum()
        changed_ct = seg_evo_df['changed'].sum()
        upgraded_ct = (seg_evo_df['direction'] == 'upgraded').sum()
        degraded_ct = (seg_evo_df['direction'] == 'degraded').sum()
        stable_ct = (seg_evo_df['direction'] == 'stable').sum()

        print(f"    Segment Evolution data built: {total_accts:,} accounts, "
              f"{n_waves} waves ({', '.join(SEG_WAVES)})")
        print(f"    Accounts with 1+ segmentation: {with_data:,}")
        print(f"    Segments discovered ({len(SEG_ORDER)}): {SEG_ORDER}")
        print(f"    Segment ranking (low-to-high): "
              f"{' < '.join(SEG_ORDER)}")
        print(f"\n    Migration summary:")
        print(f"      Changed segment: {changed_ct:,} "
              f"({changed_ct / with_data * 100:.1f}%)" if with_data else "")
        print(f"      Upgraded:  {upgraded_ct:,} "
              f"({upgraded_ct / with_data * 100:.1f}%)" if with_data else "")
        print(f"      Degraded:  {degraded_ct:,} "
              f"({degraded_ct / with_data * 100:.1f}%)" if with_data else "")
        print(f"      Stable:    {stable_ct:,} "
              f"({stable_ct / with_data * 100:.1f}%)" if with_data else "")

        # Segment distribution per wave
        print(f"\n    Segment distribution by wave:")
        for col, wave in zip(SEG_COLS, SEG_WAVES):
            dist = seg_evo_df[col].astype(str).str.strip().value_counts()
            dist = dist[dist.index != '']
            dist = dist[dist.index != 'nan']
            parts = ', '.join([f"{k}: {v:,}" for k, v in dist.items()])
            print(f"      {wave}: {parts}")

except (NameError, KeyError) as e:
    print(f"    Segment evolution data not available: {e}")
    print("    Skipping segment evolution analysis.")
    seg_evo_df = pd.DataFrame()
    SEG_COLS = []
    SEG_WAVES = []
    SEG_ORDER = []
    SEG_RANK = {}
