# ===========================================================================
# EXECUTIVE SCORECARD DASHBOARD: Single-Page KPI Grid (Conference Edition)
# ===========================================================================
# Renders all KPIs from scorecard_df as a styled card grid using GridSpec
# and FancyBboxPatch. Each card shows metric name, value, RAG, and trend.

if 'scorecard_df' not in dir() or len(scorecard_df) == 0:
    print("    scorecard_df not available -- run 01_scorecard_data first")
else:
    # -------------------------------------------------------------------
    # Layout constants
    # -------------------------------------------------------------------
    N_COLS = 4
    _n_kpis = len(scorecard_df)
    _n_rows = int(np.ceil(_n_kpis / N_COLS))

    # Compute figure height: header row + KPI rows
    HEADER_HEIGHT = 1.2
    ROW_HEIGHT = 2.8
    FIG_WIDTH = 22
    FIG_HEIGHT = HEADER_HEIGHT + (_n_rows * ROW_HEIGHT) + 1.0

    fig = plt.figure(figsize=(FIG_WIDTH, max(FIG_HEIGHT, 7)))

    # GridSpec: first row for title, remaining rows for cards
    gs = GridSpec(
        _n_rows + 1, N_COLS,
        figure=fig,
        hspace=0.35,
        wspace=0.20,
        height_ratios=[0.6] + [1.0] * _n_rows,
    )

    # -------------------------------------------------------------------
    # Title area (spans all columns in row 0)
    # -------------------------------------------------------------------
    ax_title = fig.add_subplot(gs[0, :])
    ax_title.set_xlim(0, 1)
    ax_title.set_ylim(0, 1)
    ax_title.axis('off')

    ax_title.text(
        0.0, 0.75, 'Executive Scorecard',
        fontsize=28, fontweight='bold', color=GEN_COLORS['dark_text'],
        ha='left', va='top', transform=ax_title.transAxes,
    )
    _subtitle = f"{DATASET_LABEL}" if 'DATASET_LABEL' in dir() else "Portfolio Summary"
    ax_title.text(
        0.0, 0.15, _subtitle,
        fontsize=14, fontstyle='italic', color=GEN_COLORS['muted'],
        ha='left', va='bottom', transform=ax_title.transAxes,
    )

    # RAG legend in top-right
    _legend_x = 0.75
    for _lbl, _lcolor in [('Green', GEN_COLORS['success']),
                           ('Amber', GEN_COLORS['warning']),
                           ('Red', GEN_COLORS['accent'])]:
        ax_title.plot(
            _legend_x, 0.45, 's', color=_lcolor, markersize=12,
            transform=ax_title.transAxes,
        )
        ax_title.text(
            _legend_x + 0.02, 0.45, _lbl,
            fontsize=12, fontweight='bold', color=GEN_COLORS['dark_text'],
            ha='left', va='center', transform=ax_title.transAxes,
        )
        _legend_x += 0.08

    # -------------------------------------------------------------------
    # RAG and trend color maps
    # -------------------------------------------------------------------
    RAG_COLORS = {
        'Green': GEN_COLORS['success'],
        'Amber': GEN_COLORS['warning'],
        'Red': GEN_COLORS['accent'],
    }
    RAG_BG_ALPHA = 0.08

    TREND_ARROWS = {
        'up': ('$\\uparrow$', GEN_COLORS['success']),
        'down': ('$\\downarrow$', GEN_COLORS['accent']),
        'flat': ('$\\rightarrow$', GEN_COLORS['muted']),
    }

    # Category header colors
    CAT_COLORS = {
        'Attrition': GEN_COLORS['accent'],
        'Balance': GEN_COLORS['info'],
        'Interchange': GEN_COLORS['warning'],
        'Reg E': GEN_COLORS['success'],
        'Payroll': GEN_COLORS['primary'],
        'Relationship': '#457B9D',
        'Segmentation': '#264653',
        'Retention': '#E76F51',
        'Engagement': '#2A9D8F',
    }

    # -------------------------------------------------------------------
    # Render each KPI card
    # -------------------------------------------------------------------
    for idx, row in scorecard_df.iterrows():
        _grid_row = idx // N_COLS + 1  # +1 because row 0 is title
        _grid_col = idx % N_COLS

        ax = fig.add_subplot(gs[_grid_row, _grid_col])
        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        _rag = row['rag']
        _edge_color = RAG_COLORS.get(_rag, GEN_COLORS['muted'])
        _fill_color = _edge_color

        # FancyBboxPatch background card
        _card = FancyBboxPatch(
            (0.03, 0.03), 0.94, 0.94,
            boxstyle="round,pad=0.04",
            facecolor=_fill_color,
            edgecolor=_edge_color,
            alpha=RAG_BG_ALPHA,
            linewidth=2.5,
            transform=ax.transAxes,
            clip_on=False,
        )
        ax.add_patch(_card)

        # Solid edge border on top of the alpha fill
        _border = FancyBboxPatch(
            (0.03, 0.03), 0.94, 0.94,
            boxstyle="round,pad=0.04",
            facecolor='none',
            edgecolor=_edge_color,
            linewidth=2.5,
            transform=ax.transAxes,
            clip_on=False,
        )
        ax.add_patch(_border)

        # Category label (top of card)
        _cat_color = CAT_COLORS.get(row['category'], GEN_COLORS['dark_text'])
        ax.text(
            0.50, 0.90, row['category'].upper(),
            fontsize=9, fontweight='bold', color=_cat_color,
            ha='center', va='top', transform=ax.transAxes,
            alpha=0.8,
        )

        # Metric name
        ax.text(
            0.50, 0.72, row['metric_name'],
            fontsize=11, fontweight='bold', color=GEN_COLORS['dark_text'],
            ha='center', va='top', transform=ax.transAxes,
        )

        # Value (large, colored by RAG)
        ax.text(
            0.42, 0.38, row['display'],
            fontsize=24, fontweight='bold', color=_edge_color,
            ha='center', va='center', transform=ax.transAxes,
        )

        # Trend arrow
        _arrow_sym, _arrow_color = TREND_ARROWS.get(row['trend'], ('--', GEN_COLORS['muted']))
        ax.text(
            0.82, 0.38, _arrow_sym,
            fontsize=22, fontweight='bold', color=_arrow_color,
            ha='center', va='center', transform=ax.transAxes,
        )

        # RAG badge at bottom
        ax.text(
            0.50, 0.10, _rag,
            fontsize=10, fontweight='bold', color=_edge_color,
            ha='center', va='center', transform=ax.transAxes,
            bbox=dict(
                boxstyle='round,pad=0.3',
                facecolor=_edge_color,
                alpha=0.12,
                edgecolor='none',
            ),
        )

    plt.tight_layout()
    plt.show()

    # -------------------------------------------------------------------
    # Insight callouts
    # -------------------------------------------------------------------
    _red_kpis = scorecard_df[scorecard_df['rag'] == 'Red']
    _amber_kpis = scorecard_df[scorecard_df['rag'] == 'Amber']

    if len(_red_kpis) > 0:
        _red_list = ', '.join(_red_kpis['metric_name'].tolist())
        print(f"\n    INSIGHT: {len(_red_kpis)} KPI(s) at RED status requiring immediate attention: {_red_list}")

    if len(_amber_kpis) > 0:
        _amber_list = ', '.join(_amber_kpis['metric_name'].tolist())
        print(f"\n    INSIGHT: {len(_amber_kpis)} KPI(s) at AMBER status for monitoring: {_amber_list}")

    _down_kpis = scorecard_df[scorecard_df['trend'] == 'down']
    if len(_down_kpis) > 0:
        _down_list = ', '.join(_down_kpis['metric_name'].tolist())
        print(f"\n    INSIGHT: Declining trends detected in: {_down_list}")
