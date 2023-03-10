"""Based on phidl.geometry."""
from __future__ import annotations

from typing import Tuple, Union

import gdstk

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.component_layout import Polygon, _parse_layer
from gdsfactory.component_reference import ComponentReference
from gdsfactory.typings import ComponentOrReference, Int2, LayerSpec


@gf.cell
def boolean(
    A: Union[ComponentOrReference, Tuple[ComponentOrReference, ...]],
    B: Union[ComponentOrReference, Tuple[ComponentOrReference, ...]],
    operation: str,
    precision: float = 1e-4,
    num_divisions: Union[int, Int2] = (1, 1),
    layer: LayerSpec = (1, 0),
) -> Component:
    """Performs boolean operations between 2 Component/Reference/list objects.

    ``operation`` should be one of {'not', 'and', 'or', 'xor', 'A-B', 'B-A', 'A+B'}.
    Note that 'A+B' is equivalent to 'or', 'A-B' is equivalent to 'not', and
    'B-A' is equivalent to 'not' with the operands switched

    You can also use gdsfactory.drc.boolean_klayout

    Args:
        A: Component(/Reference) or list of Component(/References).
        B: Component(/Reference) or list of Component(/References).
        operation: {'not', 'and', 'or', 'xor', 'A-B', 'B-A', 'A+B'}.
        precision: float Desired precision for rounding vertex coordinates.
        num_divisions: number of divisions with which the geometry is divided into
          multiple rectangular regions. This allows for each region to be
          processed sequentially, which is more computationally efficient.
        layer: Specific layer to put polygon geometry on.

    Returns: Component with polygon(s) of the boolean operations between
      the 2 input Components performed.

    Notes
    -----
    'A+B' is equivalent to 'or'.
    'A-B' is equivalent to 'not'.
    'B-A' is equivalent to 'not' with the operands switched.

    """
    D = Component()
    A_polys = []
    B_polys = []
    A = list(A) if isinstance(A, (list, tuple)) else [A]
    B = list(B) if isinstance(B, (list, tuple)) else [B]

    for X, polys in ((A, A_polys), (B, B_polys)):
        for e in X:
            if isinstance(e, (Component, ComponentReference)):
                polys.extend(e.get_polygons())
            elif isinstance(e, Polygon):
                polys.extend(e.polygons)

    layer = gf.pdk.get_layer(layer)
    gds_layer, gds_datatype = _parse_layer(layer)

    operation = operation.lower().replace(" ", "")
    if operation == "a-b":
        operation = "not"
    elif operation == "b-a":
        operation = "not"
        A_polys, B_polys = B_polys, A_polys
    elif operation == "a+b":
        operation = "or"
    elif operation not in ["not", "and", "or", "xor", "a-b", "b-a", "a+b"]:
        raise ValueError(
            "gdsfactory.geometry.boolean() `operation` "
            "parameter not recognized, must be one of the "
            "following:  'not', 'and', 'or', 'xor', 'A-B', "
            "'B-A', 'A+B'"
        )

    # Check for trivial solutions
    if (not A_polys or not B_polys) and operation != "or":
        if (
            operation != "not"
            and operation != "and"
            and operation == "xor"
            and not A_polys
            and not B_polys
            or operation != "not"
            and operation == "and"
        ):
            p = None
        elif operation != "not" and operation == "xor" and not A_polys:
            p = B_polys
        elif operation != "not" and operation == "xor":
            p = A_polys
        elif operation == "not":
            p = A_polys or None
    elif not A_polys and not B_polys:
        p = None
    else:
        p = gdstk.boolean(
            operand1=A_polys,
            operand2=B_polys,
            operation=operation,
            precision=precision,
            layer=gds_layer,
            datatype=gds_datatype,
        )

    if p is not None:
        polygons = D.add_polygon(p, layer=layer)
        [polygon.fracture(precision=precision) for polygon in polygons]
    return D


def test_boolean() -> None:
    c = gf.Component()
    e1 = c << gf.components.ellipse()
    e2 = c << gf.components.ellipse(radii=(10, 6))
    e3 = c << gf.components.ellipse(radii=(10, 4))
    e3.movex(5)
    e2.movex(2)
    c = boolean(A=[e1, e3], B=e2, operation="A-B")
    assert len(c.polygons) == 2, len(c.polygons)


if __name__ == "__main__":
    # c = gf.Component()
    # e1 = c << gf.components.ellipse()
    # e2 = c << gf.components.ellipse(radii=(10, 6))
    # e3 = c << gf.components.ellipse(radii=(10, 4))
    # e3.movex(5)
    # e2.movex(2)
    # c = boolean(A=[e1, e3], B=e2, operation="A-B")

    import time

    n = 50
    c1 = gf.c.array(gf.c.circle(radius=10), columns=n, rows=n)
    c2 = gf.c.array(gf.c.circle(radius=9), columns=n, rows=n).movex(5)

    t0 = time.time()
    c = boolean(c1, c2, operation="xor")
    t1 = time.time()
    print(t1 - t0)

    c.show(show_ports=True)
