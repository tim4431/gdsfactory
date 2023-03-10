from __future__ import annotations

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.typings import Floats, LayerSpec


@gf.cell
def verniers(
    widths: Floats = (0.1, 0.2, 0.3, 0.4, 0.5),
    gap: float = 0.1,
    xsize: int = 100,
    layer_label: LayerSpec = "LABEL",
    **kwargs,
) -> Component:
    c = gf.Component()
    y = 0

    for width in widths:
        w = c << gf.components.straight(width=width, length=xsize, **kwargs)
        y += width / 2
        w.y = y
        c.add_label(text=str(int(width * 1e3)), position=(0, y), layer=layer_label)
        y += width / 2 + gap

    return c


if __name__ == "__main__":
    c = verniers()
    c.show(show_ports=True)
