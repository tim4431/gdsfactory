"""Straight Doped PIN waveguide."""
from __future__ import annotations

from typing import Optional

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.components.taper import taper_strip_to_ridge
from gdsfactory.components.via_stack import via_stack_slab_m3
from gdsfactory.cross_section import pin, pn
from gdsfactory.typings import ComponentSpec, CrossSectionSpec


@gf.cell
def straight_pin(
    length: float = 500.0,
    cross_section: CrossSectionSpec = pin,
    via_stack: ComponentSpec = via_stack_slab_m3,
    via_stack_width: float = 10.0,
    via_stack_spacing: float = 2,
    taper: Optional[ComponentSpec] = taper_strip_to_ridge,
    **kwargs,
) -> Component:
    """Returns rib waveguide with doping and via_stacks used for PN and PIN modulators.

    For PIN:
    https://doi.org/10.1364/OE.26.029983

    500um length for PI phase shift
    https://ieeexplore.ieee.org/document/8268112

    to go beyond 2PI, you will need at least 1mm
    https://ieeexplore.ieee.org/document/8853396/

    For PN:
    Typical lengths in practice are 2-5mm depending on doping,engineering and application:
    https://opg.optica.org/oe/fulltext.cfm?uri=oe-21-25-30350&id=275107
    https://opg.optica.org/oe/fulltext.cfm?uri=oe-20-11-12014&id=233271

    Args:
        length: of the waveguide.
        cross_section: for the waveguide.
        via_stack: for the via_stacks.
        via_stack_width: width of the via_stack.
        via_stack_spacing: spacing between via_stacks.
        taper: optional taper.
        kwargs: cross_section settings.
    """
    c = Component()
    if taper:
        taper = gf.get_component(taper)
        length -= 2 * taper.get_ports_xsize()

    wg = c << gf.components.straight(
        cross_section=cross_section,
        length=length,
        **kwargs,
    )

    if taper:
        t1 = c << taper
        t2 = c << taper
        t1.connect("o2", wg.ports["o1"])
        t2.connect("o2", wg.ports["o2"])
        c.add_port("o1", port=t1.ports["o1"])
        c.add_port("o2", port=t2.ports["o1"])

    else:
        c.add_ports(wg.get_ports_list())

    via_stack_length = length
    via_stack_top = c << via_stack(
        size=(via_stack_length, via_stack_width),
    )
    via_stack_bot = c << via_stack(
        size=(via_stack_length, via_stack_width),
    )

    via_stack_bot.xmin = wg.xmin
    via_stack_top.xmin = wg.xmin

    via_stack_top.ymin = +via_stack_spacing / 2
    via_stack_bot.ymax = -via_stack_spacing / 2

    c.add_ports(via_stack_bot.ports, prefix="bot_")
    c.add_ports(via_stack_top.ports, prefix="top_")
    return c


straight_pn = gf.partial(straight_pin, cross_section=pn, length=2000)

if __name__ == "__main__":
    c = straight_pin(length=40)
    # print(c.ports.keys())
    c.show(show_ports=True)
