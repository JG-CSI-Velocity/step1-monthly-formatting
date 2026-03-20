"""Figure lifecycle management -- guaranteed cleanup + style isolation."""

from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.axes import Axes  # noqa: E402
from matplotlib.figure import Figure  # noqa: E402

_ARS_STYLE = Path(__file__).resolve().parent / "ars.mplstyle"

# Pre-load style as dict so matplotlib doesn't struggle with Windows paths
_STYLE_DICT = {}
try:
    if _ARS_STYLE.exists():
        import matplotlib as _mpl
        _STYLE_DICT = _mpl.rc_params_from_file(str(_ARS_STYLE), use_default_template=False)
except Exception:
    pass


@contextmanager
def chart_figure(
    figsize: tuple[float, float] = (10, 6),
    dpi: int = 150,
    style: str | None = None,
    save_path: Path | None = None,
) -> Generator[tuple[Figure, Axes], None, None]:
    """Context manager guaranteeing figure cleanup + style isolation.

    Usage:
        with chart_figure(save_path=out / "chart.png") as (fig, ax):
            ax.bar(x, y)
            ax.set_title("My Chart")
        # Figure is saved and closed automatically
    """
    if style:
        ctx = plt.style.context(style)
    elif _STYLE_DICT:
        ctx = plt.style.context(_STYLE_DICT)
    else:
        ctx = plt.style.context('default')

    with ctx:
        fig, ax = plt.subplots(figsize=figsize, dpi=dpi)
        try:
            yield fig, ax
            if save_path is not None:
                fig.savefig(save_path, dpi=dpi, bbox_inches="tight")
        finally:
            plt.close(fig)
