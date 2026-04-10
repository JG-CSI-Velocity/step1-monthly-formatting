# ===========================================================================
# RISK BY DEMOGRAPHICS: 3-Panel Breakdown (Conference Edition)
# ===========================================================================
# Panel 1: Risk tier by age band
# Panel 2: Risk tier by account age band
# Panel 3: Risk tier by engagement tier

# ---------------------------------------------------------------------------
# Prepare demographic merges
# ---------------------------------------------------------------------------
AGE_BINS = [18, 26, 36, 46, 56, 66, 200]
AGE_BAND_LABELS = ['18-25', '26-35', '36-45', '46-55', '56-65', '65+']

# Age band from holder_age in attrition_df
_demo = attrition_df.copy()
if 'holder_age' in _demo.columns:
    _demo['age_band'] = pd.cut(
        _demo['holder_age'], bins=AGE_BINS, labels=AGE_BAND_LABELS, right=False
    )
else:
    _demo['age_band'] = 'Unknown'

# Account age band: merge from rewards_df if available
if 'Account Age' in rewards_df.columns:
    _acct_age = rewards_df[['Acct Number', 'Account Age']].copy()
    _acct_age.columns = ['account_number', 'account_age']
    _acct_age['account_age'] = pd.to_numeric(_acct_age['account_age'], errors='coerce')
    _demo = _demo.merge(_acct_age, on='account_number', how='left')

    _acct_age_bins = [0, 91, 181, 366, 731, 1096, 1826, 3651, 7301, 999999]
    _demo['acct_age_band'] = pd.cut(
        _demo['account_age'], bins=_acct_age_bins, labels=ACCT_AGE_ORDER, right=False
    )
else:
    _demo['acct_age_band'] = 'Unknown'

# Engagement tier: merge from acct_txn_counts if available
if 'acct_txn_counts' in dir() or 'acct_txn_counts' in globals():
    _eng_map = acct_txn_counts[['account', 'tier']].copy()
    _eng_map.columns = ['account_number', 'engage_tier']
    _demo = _demo.merge(_eng_map, on='account_number', how='left')
    _demo['engage_tier'] = _demo['engage_tier'].fillna('Unknown')
else:
    _demo['engage_tier'] = 'Unknown'

# ---------------------------------------------------------------------------
# Helper: build stacked proportions
# ---------------------------------------------------------------------------
def _build_stacked(df, group_col, group_order, tier_col='risk_tier'):
    """Build stacked percentage DataFrame for a grouping column."""
    ct = pd.crosstab(df[group_col], df[tier_col], normalize='index') * 100
    # Reorder columns
    ct = ct.reindex(columns=[t for t in RISK_ORDER if t in ct.columns], fill_value=0)
    # Reorder rows
    _valid_order = [g for g in group_order if g in ct.index]
    if _valid_order:
        ct = ct.reindex(_valid_order)
    return ct

# ---------------------------------------------------------------------------
# 3-Panel figure
# ---------------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(22, 8))

# Panel 1: Age band
if 'age_band' in _demo.columns and _demo['age_band'].notna().sum() > 0:
    _age_ct = _build_stacked(_demo.dropna(subset=['age_band']), 'age_band', AGE_ORDER)
    _age_ct.plot(
        kind='barh', stacked=True, ax=axes[0],
        color=[RISK_PALETTE[t] for t in _age_ct.columns],
        edgecolor='white', linewidth=0.5,
    )
    axes[0].set_xlabel("% of Accounts", fontsize=14, fontweight='bold')
    axes[0].set_title("By Age Band", fontsize=18, fontweight='bold',
                      color=GEN_COLORS['dark_text'], pad=15, loc='left')
    axes[0].legend_.remove()
else:
    axes[0].text(0.5, 0.5, "No age data available", transform=axes[0].transAxes,
                 ha='center', va='center', fontsize=14, color=GEN_COLORS['muted'])
    axes[0].set_title("By Age Band", fontsize=18, fontweight='bold',
                      color=GEN_COLORS['dark_text'], pad=15, loc='left')

# Panel 2: Account age band
if 'acct_age_band' in _demo.columns and _demo['acct_age_band'].notna().sum() > 0:
    _acct_ct = _build_stacked(
        _demo.dropna(subset=['acct_age_band']), 'acct_age_band', ACCT_AGE_ORDER
    )
    _acct_ct.plot(
        kind='barh', stacked=True, ax=axes[1],
        color=[RISK_PALETTE[t] for t in _acct_ct.columns],
        edgecolor='white', linewidth=0.5,
    )
    axes[1].set_xlabel("% of Accounts", fontsize=14, fontweight='bold')
    axes[1].set_title("By Account Age", fontsize=18, fontweight='bold',
                      color=GEN_COLORS['dark_text'], pad=15, loc='left')
    axes[1].legend_.remove()
else:
    axes[1].text(0.5, 0.5, "No account age data", transform=axes[1].transAxes,
                 ha='center', va='center', fontsize=14, color=GEN_COLORS['muted'])
    axes[1].set_title("By Account Age", fontsize=18, fontweight='bold',
                      color=GEN_COLORS['dark_text'], pad=15, loc='left')

# Panel 3: Engagement tier
if 'engage_tier' in _demo.columns and _demo['engage_tier'].notna().sum() > 0:
    _eng_ct = _build_stacked(
        _demo[_demo['engage_tier'] != 'Unknown'], 'engage_tier', ENGAGE_ORDER
    )
    _eng_ct.plot(
        kind='barh', stacked=True, ax=axes[2],
        color=[RISK_PALETTE[t] for t in _eng_ct.columns],
        edgecolor='white', linewidth=0.5,
    )
    axes[2].set_xlabel("% of Accounts", fontsize=14, fontweight='bold')
    axes[2].set_title("By Engagement Tier", fontsize=18, fontweight='bold',
                      color=GEN_COLORS['dark_text'], pad=15, loc='left')
    axes[2].legend_.remove()
else:
    axes[2].text(0.5, 0.5, "No engagement data", transform=axes[2].transAxes,
                 ha='center', va='center', fontsize=14, color=GEN_COLORS['muted'])
    axes[2].set_title("By Engagement Tier", fontsize=18, fontweight='bold',
                      color=GEN_COLORS['dark_text'], pad=15, loc='left')

# Clean all axes
for ax in axes:
    gen_clean_axes(ax, keep_left=True, keep_bottom=True)

# Shared legend at bottom
_legend_handles = [
    plt.Rectangle((0, 0), 1, 1, facecolor=RISK_PALETTE[t], edgecolor='white')
    for t in RISK_ORDER
]
fig.legend(_legend_handles, RISK_ORDER, loc='lower center',
           ncol=len(RISK_ORDER), fontsize=13, frameon=False,
           bbox_to_anchor=(0.5, -0.02))

fig.suptitle("Risk Tier by Demographics",
             fontsize=26, fontweight='bold',
             color=GEN_COLORS['dark_text'], y=1.03)
fig.text(0.5, 0.99, f"Which segments have the highest attrition risk? | {DATASET_LABEL}",
         fontsize=14, color=GEN_COLORS['muted'], style='italic', ha='center')

plt.tight_layout()
plt.show()

# Callout
if 'age_band' in _demo.columns and _demo['age_band'].notna().sum() > 0:
    _age_risk = _demo[_demo['age_band'].notna()].groupby('age_band')['risk_tier'].apply(
        lambda x: (x.isin(['Declining', 'Dormant'])).mean() * 100
    )
    _worst_band = _age_risk.idxmax()
    print(f"\n    INSIGHT: Highest at-risk rate by age: {_worst_band} "
          f"({_age_risk[_worst_band]:.1f}% declining/dormant)")
