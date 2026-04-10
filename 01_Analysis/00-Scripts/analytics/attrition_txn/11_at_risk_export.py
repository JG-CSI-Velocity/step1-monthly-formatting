# ===========================================================================
# AT-RISK EXPORT: Top 100 Declining/Dormant by Balance (Conference Edition)
# ===========================================================================
# Styled table of highest-value at-risk accounts for action.

# ---------------------------------------------------------------------------
# Filter at-risk accounts and sort by balance
# ---------------------------------------------------------------------------
_at_risk = attrition_df[attrition_df['risk_tier'].isin(['Declining', 'Dormant'])].copy()

# Determine sort column (prefer avg_bal, fall back to last_12mo_spend)
_sort_col = None
if 'avg_bal' in _at_risk.columns and _at_risk['avg_bal'].sum() > 0:
    _sort_col = 'avg_bal'
elif 'last_12mo_spend' in _at_risk.columns and _at_risk['last_12mo_spend'].sum() > 0:
    _sort_col = 'last_12mo_spend'

if _sort_col:
    _at_risk = _at_risk.sort_values(_sort_col, ascending=False)

# Select top 100
_top100 = _at_risk.head(100).copy()

# Build display columns
_display_cols = ['account_number', 'risk_tier']
_format_map = {}

if 'avg_bal' in _top100.columns:
    _display_cols.append('avg_bal')
    _format_map['avg_bal'] = '${:,.0f}'

if 'last_3mo_spend' in _top100.columns:
    _display_cols.append('last_3mo_spend')
    _format_map['last_3mo_spend'] = '${:,.0f}'

if 'last_12mo_spend' in _top100.columns:
    _display_cols.append('last_12mo_spend')
    _format_map['last_12mo_spend'] = '${:,.0f}'

_display_cols.append('spend_velocity')
_format_map['spend_velocity'] = '{:.2f}x'

if 'prod_desc' in _top100.columns:
    _display_cols.append('prod_desc')
elif 'prod_code' in _top100.columns:
    _display_cols.append('prod_code')

# Filter to available columns
_display_cols = [c for c in _display_cols if c in _top100.columns]
_export_df = _top100[_display_cols].reset_index(drop=True)

# Rename for display
_rename_map = {
    'account_number': 'Account',
    'risk_tier': 'Risk Tier',
    'avg_bal': 'Avg Balance',
    'last_3mo_spend': '3-Mo Spend',
    'last_12mo_spend': '12-Mo Spend',
    'spend_velocity': 'Velocity',
    'prod_desc': 'Product',
    'prod_code': 'Product',
}
_export_df = _export_df.rename(columns={c: _rename_map.get(c, c) for c in _export_df.columns})

# Update format map keys
_format_display = {}
for k, v in _format_map.items():
    _new_key = _rename_map.get(k, k)
    if _new_key in _export_df.columns:
        _format_display[_new_key] = v

# ---------------------------------------------------------------------------
# Risk tier color styling
# ---------------------------------------------------------------------------
def _risk_color(val):
    """Color risk tier values."""
    if val == 'Declining':
        return f"color: {GEN_COLORS['warning']}; font-weight: bold"
    if val == 'Dormant':
        return f"color: {GEN_COLORS['muted']}; font-weight: bold"
    return f"color: {GEN_COLORS['dark_text']}; font-weight: bold"

# ---------------------------------------------------------------------------
# Styled table
# ---------------------------------------------------------------------------
styled = (
    _export_df.style
    .hide(axis='index')
    .format(_format_display)
    .set_properties(**{
        'font-size': '13px',
        'font-weight': 'bold',
        'text-align': 'center',
        'border': '1px solid #E9ECEF',
        'padding': '8px 12px',
    })
    .set_table_styles([
        {'selector': 'th', 'props': [
            ('background-color', GEN_COLORS['primary']),
            ('color', 'white'),
            ('font-size', '14px'),
            ('font-weight', 'bold'),
            ('text-align', 'center'),
            ('padding', '10px 14px'),
        ]},
        {'selector': 'caption', 'props': [
            ('font-size', '22px'),
            ('font-weight', 'bold'),
            ('color', GEN_COLORS['dark_text']),
            ('text-align', 'left'),
            ('padding-bottom', '12px'),
        ]},
    ])
    .set_caption("Top 100 At-Risk Accounts (by Balance)")
)

if 'Risk Tier' in _export_df.columns:
    styled = styled.applymap(_risk_color, subset=['Risk Tier'])

# Add balance bar if available
if 'Avg Balance' in _export_df.columns:
    styled = styled.bar(subset=['Avg Balance'], color=GEN_COLORS['accent'], vmin=0, width=80)

display(styled)

# ---------------------------------------------------------------------------
# Summary callouts
# ---------------------------------------------------------------------------
print(f"\n    Top 100 at-risk accounts displayed (sorted by {'balance' if _sort_col == 'avg_bal' else 'annual spend'})")
print(f"    Full list available in attrition_df (filter: risk_tier in ['Declining', 'Dormant'])")
print(f"    Total at-risk accounts: {len(_at_risk):,}")
if 'avg_bal' in _at_risk.columns:
    print(f"    Total balance at risk: {gen_fmt_dollar(_at_risk['avg_bal'].sum(), None)}")
if 'last_12mo_spend' in _at_risk.columns:
    print(f"    Total annual spend at risk: {gen_fmt_dollar(_at_risk['last_12mo_spend'].sum(), None)}")
