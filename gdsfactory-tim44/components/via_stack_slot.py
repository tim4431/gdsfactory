from __future__ import annotations

from typing import Optional

from numpy import floor

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.components.compass import compass
from gdsfactory.components.via import via1, viac
from gdsfactory.typings import ComponentSpec, Floats, LayerSpec, LayerSpecs


@gf.cell
def via_stack_slot(
    size=(11.0, 11.0),
    layers: LayerSpecs = ("M1", "M2"),
    layer_offsets: Optional[Floats] = (0, 1.0),
    layer_offsetsx: Optional[Floats] = None,
    layer_offsetsy: Optional[Floats] = None,
    layer_port: LayerSpec = None,
    via: ComponentSpec = via1,
    enclosure: float = 1.0,
    ysize: float = 0.5,
    yspacing: float = 2.0,
) -> Component:
    """Rectangular via_stack with slotted via in X direction.

    Args:
        size: of the layers.
        layers: layers on which to draw rectangles.
        layer_offsets: cladding_offset for each layer.
        layer_offsetsx: optional xoffset for layers, defaults to layer_offsets.
        layer_offsetsx: optional yoffset for layers, defaults to layer_offsets.
        layer_port: if None assumes port is on the last layer.
        via: via to use to fill the rectangles.
        enclosure: of the via by rectangle.
        ysize: via height in y.
        yspacing: via spacing pitch in y.

    .. code::

         __________________________________________
        |                |                        |
        |                | layer_offsetsy[1]      |
        |  ______________|______________________  |
        |  |<--->                              |<>|
        |  |enclosure                          | layer_offsetsx[1]
        |  |      ______________________       |  |
        |  |     |                      |      |  |
        |  |     |     via              | ysize|  |
        |  |     |______________________|      |  |
        |  |  |                                |  |
        |  |  | yspacing                size[1]|  |
        |  |  |                                |  |
        |  |  |   ______________________       |  |
        |  |  |  |                      |      |  |
        |  |  |  |     via              | ysize|  |
        |  |  |  |______________________|      |  |
        |  |                                   |  |
        |  |                                   |  |
        |  |___________________________________|  |
        |                  size[0]                |
        |                                         |
        |_________________________________________|
    """
    if size[0] - 2 * enclosure < 0:
        raise ValueError(
            f"via_stack length (size[0] = {size[0]}) < 2*enclosure ({2*enclosure}). "
        )
    if size[1] - 2 * enclosure < 0:
        raise ValueError(
            f"via_stack width (size[1] = {size[1]}) < 2*enclosure ({2*enclosure}). "
        )

    layer_port = layer_port or layers[-1]

    c = Component()
    c.info["size"] = (float(size[0]), float(size[1]))

    layer_offsetsx = layer_offsetsx or layer_offsets
    layer_offsetsy = layer_offsetsy or layer_offsets

    layer_offsetsx = list(layer_offsetsx) + [0] * len(layers)
    layer_offsetsy = list(layer_offsetsy) + [0] * len(layers)

    for layer, offsetx, offsety in zip(layers, layer_offsetsx, layer_offsetsy):
        ref = c << compass(
            size=(size[0] + 2 * offsetx, size[1] + 2 * offsety), layer=layer
        )

        if layer == layer_port:
            c.add_ports(ref.ports)

    via = gf.get_component(via, size=(size[0] - 2 * enclosure, ysize))

    nb_vias_y = (size[1] - 2 * enclosure) / yspacing
    nb_vias_y = int(floor(nb_vias_y)) or 1
    ref = c.add_array(via, columns=1, rows=nb_vias_y, spacing=(0, yspacing))
    dy = (size[1] - (nb_vias_y - 1) * yspacing - size[1]) / 2
    ref.move((0, dy))
    return c


via_stack_slot_m1_m2 = gf.partial(via_stack_slot, layers=("M1", "M2"), via=via1)

via_stack_slot_slab_m1 = gf.partial(via_stack_slot, layers=("M1",), via=viac)


if __name__ == "__main__":
    # c = via_stack_slot_m1_m2(layer_offsets=(0.5, 1), enclosure=1, size=(3, 3))
    # c = via_stack_slot_m1_m2()
    c = via_stack_slot_slab_m1()
    c.show(show_ports=True)
