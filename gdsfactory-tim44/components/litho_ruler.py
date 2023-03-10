from __future__ import annotations

from typing import Tuple

import gdsfactory as gf
from gdsfactory.typings import LayerSpec


@gf.cell
def litho_ruler(
    height: float = 2,
    width: float = 0.5,
    spacing: float = 2.0,
    scale: Tuple[float, ...] = (3, 1, 1, 1, 1, 2, 1, 1, 1, 1),
    num_marks: int = 21,
    layer: LayerSpec = "WG",
) -> gf.Component:
    """Ruler structure for lithographic measurement.

    Includes marks of varying scales to allow for easy reading by eye.

    based on phidl.geometry

    Args:
        height: Height of the ruling marks in um.
        width: Width of the ruling marks in um.
        spacing: Center-to-center spacing of the ruling marks in um.
        scale: Height scale pattern of marks.
        num_marks: Total number of marks to generate.
        layer: Specific layer to put the ruler geometry on.
    """
    D = gf.Component()
    for n in range(num_marks):
        h = height * scale[n % len(scale)]
        D << gf.components.rectangle(size=(width, h), layer=layer)

    D.distribute(direction="x", spacing=spacing, separation=False, edge="x")
    D.align(alignment="ymin")
    D.flatten()
    return D


if __name__ == "__main__":
    c = litho_ruler()
    c.show(show_ports=True)
