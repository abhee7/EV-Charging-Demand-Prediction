"""One registered Plotly template, so charts carry no repeated layout kwargs."""

from __future__ import annotations

import plotly.graph_objects as go
import plotly.io as pio

import config

TEMPLATE_NAME = "chargecast"
_FONT = ("Inter, 'Space Grotesk', -apple-system, BlinkMacSystemFont, "
         "'Segoe UI', sans-serif")


def register() -> None:
    if TEMPLATE_NAME in pio.templates:
        return

    axis = dict(
        gridcolor=config.GRID,
        zerolinecolor=config.GRID,
        linecolor=config.GRID,
        tickfont=dict(color=config.TEXT_MUTED, size=11),
        title=dict(font=dict(color=config.TEXT_MUTED, size=12)),
        showline=False,
    )

    pio.templates[TEMPLATE_NAME] = go.layout.Template(
        layout=go.Layout(
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family=_FONT, color=config.TEXT, size=12),
            title=dict(font=dict(size=15, color=config.TEXT), x=0,
                       xanchor="left"),
            xaxis=axis,
            yaxis=axis,
            colorway=config.FALLBACK_CYCLE,
            margin=dict(l=8, r=8, t=46, b=8),
            hoverlabel=dict(bgcolor=config.SURFACE, bordercolor=config.CYAN,
                            font=dict(color=config.TEXT, family=_FONT,
                                      size=12)),
            legend=dict(orientation="h", yanchor="bottom", y=1.02,
                        xanchor="left", x=0, bgcolor="rgba(0,0,0,0)",
                        font=dict(color=config.TEXT_MUTED, size=11)),
            hovermode="x unified",
        )
    )
    pio.templates.default = TEMPLATE_NAME


HEATMAP_SCALE = [
    [0.00, "#0B1316"],
    [0.25, "#0E3A3C"],
    [0.55, "#0F6E68"],
    [0.80, "#12A897"],
    [1.00, config.CYAN],
]


def apply(fig: go.Figure, height: int = 320, **kwargs) -> go.Figure:
    fig.update_layout(template=TEMPLATE_NAME, height=height, **kwargs)
    return fig
