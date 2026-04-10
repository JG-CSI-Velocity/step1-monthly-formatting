# ===========================================================================
# INTERCHANGE BY DEMOGRAPHICS -- 3 PANEL
# ===========================================================================
# (1) SIG ratio by age band
# (2) SIG ratio by product type
# (3) SIG ratio by business vs personal

active = interchange_df[
    (interchange_df['total_pin_dollars'] + interchange_df['total_sig_dollars']) > 0
].copy()

active['sig_ratio_pct'] = active['sig_ratio'] * 100

# -----------------------------------------------------------------------
# Panel 1: Age bands
# -----------------------------------------------------------------------
has_age = ('Account Holder Age' in active.columns
           and active['Account Holder Age'].notna().sum() > 0)

if has_age:
    age = pd.to_numeric(active['Account Holder Age'], errors='coerce')
    bins = [0, 25, 35, 45, 55, 65, 120]
    labels_age = ['18-25', '26-35', '36-45', '46-55', '56-65', '65+']
    active['age_band'] = pd.cut(age, bins=bins, labels=labels_age, right=True)

# -----------------------------------------------------------------------
# Panel 2: Product type (top N)
# -----------------------------------------------------------------------
has_prod = ('Prod Desc' in active.columns
            and active['Prod Desc'].notna().sum() > 0)
if not has_prod:
    has_prod = ('Prod Code' in active.columns
                and active['Prod Code'].notna().sum() > 0)
    prod_col = 'Prod Code' if has_prod else None
else:
    prod_col = 'Prod Desc'

# -----------------------------------------------------------------------
# Panel 3: Business vs Personal
# -----------------------------------------------------------------------
has_biz = ('Business?' in active.columns
           and active['Business?'].notna().sum() > 0)

# -----------------------------------------------------------------------
# Build 3-panel figure
# -----------------------------------------------------------------------
fig, axes = plt.subplots(1, 3, figsize=(20, 7))

# -- PANEL 1: Age Band ------------------------------------------------
ax = axes[0]
if has_age:
    age_agg = (
        active.groupby('age_band', observed=True)
        .agg(
            sig_dollars=('total_sig_dollars', 'sum'),
            total_dollars=('total_pin_dollars', lambda s: s.sum()),
            sig_d2=('total_sig_dollars', 'sum'),
            count=('acct_number', 'count'),
        )
    )
    age_agg['total'] = age_agg['total_dollars'] + age_agg['sig_d2']
    age_agg['sig_ratio'] = np.where(
        age_agg['total'] > 0,
        age_agg['sig_dollars'] / age_agg['total'] * 100, 0)
    age_agg = age_agg.reindex(
        [l for l in labels_age if l in age_agg.index])

    bar_colors = [AGE_PALETTE.get(b, GEN_COLORS['info']) for b in age_agg.index]
    bars = ax.bar(age_agg.index, age_agg['sig_ratio'],
                  color=bar_colors, alpha=0.85, width=0.6)
    for bar, val, cnt in zip(bars, age_agg['sig_ratio'], age_agg['count']):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{val:.1f}%\n(n={cnt:,})", ha='center', va='bottom',
                fontsize=10, fontweight='bold', color=GEN_COLORS['dark_text'])
    ax.set_title('SIG Ratio by Age Band', fontsize=18, fontweight='bold',
                 loc='left')
    ax.set_ylabel('SIG Ratio (%)', fontsize=14, fontweight='bold')
else:
    ax.text(0.5, 0.5, 'Age data not available',
            ha='center', va='center', fontsize=14, color=GEN_COLORS['muted'],
            transform=ax.transAxes)
    ax.set_title('SIG Ratio by Age Band', fontsize=18, fontweight='bold',
                 loc='left')
ax.set_ylim(0, 100)
ax.axhline(60, color=GEN_COLORS['success'], linestyle='--', alpha=0.4)
ax.axhline(40, color=GEN_COLORS['accent'], linestyle='--', alpha=0.4)
gen_clean_axes(ax)

# -- PANEL 2: Product Type --------------------------------------------
ax = axes[1]
if has_prod and prod_col:
    prod_agg = (
        active.groupby(prod_col)
        .agg(
            sig_dollars=('total_sig_dollars', 'sum'),
            pin_dollars=('total_pin_dollars', 'sum'),
            count=('acct_number', 'count'),
        )
    )
    prod_agg['total'] = prod_agg['pin_dollars'] + prod_agg['sig_dollars']
    prod_agg['sig_ratio'] = np.where(
        prod_agg['total'] > 0,
        prod_agg['sig_dollars'] / prod_agg['total'] * 100, 0)
    prod_agg = prod_agg[prod_agg['count'] >= 10].sort_values(
        'sig_ratio', ascending=True).tail(10)

    y_pos = np.arange(len(prod_agg))
    bar_colors = [GEN_COLORS['success'] if v >= 60
                  else (GEN_COLORS['warning'] if v >= 40
                        else GEN_COLORS['accent'])
                  for v in prod_agg['sig_ratio']]
    bars = ax.barh(y_pos, prod_agg['sig_ratio'],
                   color=bar_colors, alpha=0.85, height=0.6)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(prod_agg.index, fontsize=10)
    for bar, val, cnt in zip(bars, prod_agg['sig_ratio'], prod_agg['count']):
        ax.text(bar.get_width() + 1, bar.get_y() + bar.get_height() / 2,
                f"{val:.1f}% (n={cnt:,})", va='center',
                fontsize=10, fontweight='bold', color=GEN_COLORS['dark_text'])
    ax.axvline(60, color=GEN_COLORS['success'], linestyle='--', alpha=0.4)
    ax.axvline(40, color=GEN_COLORS['accent'], linestyle='--', alpha=0.4)
    ax.set_title('SIG Ratio by Product', fontsize=18, fontweight='bold',
                 loc='left')
    ax.set_xlabel('SIG Ratio (%)', fontsize=14, fontweight='bold')
    ax.set_xlim(0, 100)
else:
    ax.text(0.5, 0.5, 'Product data not available',
            ha='center', va='center', fontsize=14, color=GEN_COLORS['muted'],
            transform=ax.transAxes)
    ax.set_title('SIG Ratio by Product', fontsize=18, fontweight='bold',
                 loc='left')
gen_clean_axes(ax)

# -- PANEL 3: Business vs Personal ------------------------------------
ax = axes[2]
if has_biz:
    biz_agg = (
        active.groupby('Business?')
        .agg(
            sig_dollars=('total_sig_dollars', 'sum'),
            pin_dollars=('total_pin_dollars', 'sum'),
            count=('acct_number', 'count'),
        )
    )
    biz_agg['total'] = biz_agg['pin_dollars'] + biz_agg['sig_dollars']
    biz_agg['sig_ratio'] = np.where(
        biz_agg['total'] > 0,
        biz_agg['sig_dollars'] / biz_agg['total'] * 100, 0)

    bar_colors = [GEN_COLORS['primary'], GEN_COLORS['info']]
    bars = ax.bar(biz_agg.index, biz_agg['sig_ratio'],
                  color=bar_colors[:len(biz_agg)], alpha=0.85, width=0.5)
    for bar, val, cnt in zip(bars, biz_agg['sig_ratio'], biz_agg['count']):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 1.5,
                f"{val:.1f}%\n(n={cnt:,})", ha='center', va='bottom',
                fontsize=12, fontweight='bold', color=GEN_COLORS['dark_text'])
    ax.set_title('SIG Ratio: Business vs Personal',
                 fontsize=18, fontweight='bold', loc='left')
    ax.set_ylabel('SIG Ratio (%)', fontsize=14, fontweight='bold')
    ax.set_ylim(0, 100)
    ax.axhline(60, color=GEN_COLORS['success'], linestyle='--', alpha=0.4)
    ax.axhline(40, color=GEN_COLORS['accent'], linestyle='--', alpha=0.4)
else:
    ax.text(0.5, 0.5, 'Business flag not available',
            ha='center', va='center', fontsize=14, color=GEN_COLORS['muted'],
            transform=ax.transAxes)
    ax.set_title('SIG Ratio: Business vs Personal',
                 fontsize=18, fontweight='bold', loc='left')
gen_clean_axes(ax)

fig.suptitle("Signature Ratio by Demographics",
             fontsize=24, fontweight='bold', x=0.02, ha='left',
             color=GEN_COLORS['dark_text'])
fig.text(0.02, 0.93,
         f"Who routes SIG vs PIN?  |  {DATASET_LABEL}",
         fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
         ha='left')

plt.tight_layout(rect=[0, 0, 1, 0.90])
plt.show()
