from __future__ import annotations

from typing import Optional

import gdsfactory as gf
from gdsfactory.cell import cell
from gdsfactory.component import Component
from gdsfactory.typings import ComponentSpec, CrossSectionSpec


@cell
def straight_heater_metal_undercut(
    length: float = 320.0,
    length_undercut_spacing: float = 6.0,
    length_undercut: float = 30.0,
    length_straight_input: float = 15.0,
    heater_width: float = 2.5,
    cross_section_heater: CrossSectionSpec = "heater_metal",
    cross_section_waveguide_heater: CrossSectionSpec = "strip_heater_metal",
    cross_section_heater_undercut: CrossSectionSpec = "strip_heater_metal_undercut",
    with_undercut: bool = True,
    via_stack: Optional[ComponentSpec] = "via_stack_heater_mtop",
    port_orientation1: int = 180,
    port_orientation2: int = 0,
    heater_taper_length: Optional[float] = 5.0,
    ohms_per_square: Optional[float] = None,
    cross_section: Optional[CrossSectionSpec] = None,
    **kwargs,
) -> Component:
    """Returns a thermal phase shifter.

    dimensions from https://doi.org/10.1364/OE.27.010456

    Args:
        length: of the waveguide.
        length_undercut_spacing: from undercut regions.
        length_undercut: length of each undercut section.
        length_straight_input: from input port to where trenches start.
        heater_width: in um.
        cross_section_heater: for heated sections. heater metal only.
        cross_section_waveguide_heater: for heated sections.
        cross_section_heater_undercut: for heated sections with undercut.
        with_undercut: isolation trenches for higher efficiency.
        via_stack: via stack.
        port_orientation1: left via stack port orientation.
        port_orientation2: right via stack port orientation.
        heater_taper_length: minimizes current concentrations from heater to via_stack.
        ohms_per_square: to calculate resistance.
        cross_section: for waveguide ports.
        kwargs: cross_section common settings.
    """
    period = length_undercut + length_undercut_spacing
    n = int((length - 2 * length_straight_input) // period)

    length_straight_input = (length - n * period) / 2

    s_si = gf.components.straight(
        cross_section=cross_section_waveguide_heater,
        length=length_straight_input,
        heater_width=heater_width,
        **kwargs,
    )
    cross_section_undercut = (
        cross_section_heater_undercut
        if with_undercut
        else cross_section_waveguide_heater
    )
    s_uc = gf.components.straight(
        cross_section=cross_section_undercut,
        length=length_undercut,
        heater_width=heater_width,
        **kwargs,
    )
    s_spacing = gf.components.straight(
        cross_section=cross_section_waveguide_heater,
        length=length_undercut_spacing,
        heater_width=heater_width,
        **kwargs,
    )
    symbol_to_component = {
        "-": (s_si, "o1", "o2"),
        "U": (s_uc, "o1", "o2"),
        "H": (s_spacing, "o1", "o2"),
    }

    # Each character in the sequence represents a component
    sequence = "-" + n * "UH" + "-"

    c = Component()
    sequence = gf.components.component_sequence(
        sequence=sequence, symbol_to_component=symbol_to_component
    )
    c.add_ref(sequence)
    c.add_ports(sequence.ports)

    if via_stack:
        refs = list(sequence.named_references.keys())
        via_stackw = via_stacke = gf.get_component(via_stack)
        via_stack_west_center = sequence.named_references[refs[0]].size_info.cw
        via_stack_east_center = sequence.named_references[refs[-1]].size_info.ce
        dx = via_stackw.get_ports_xsize() / 2 + heater_taper_length or 0

        via_stack_west = c << via_stackw
        via_stack_east = c << via_stacke
        via_stack_west.move(via_stack_west_center - (dx, 0))
        via_stack_east.move(via_stack_east_center + (dx, 0))
        c.add_port(
            "e1", port=via_stack_west.get_ports_list(orientation=port_orientation1)[0]
        )
        c.add_port(
            "e2", port=via_stack_east.get_ports_list(orientation=port_orientation2)[0]
        )
        if heater_taper_length:
            x = gf.get_cross_section(cross_section_heater, width=heater_width)
            taper = gf.components.taper(
                width1=via_stackw.ports["e1"].width,
                width2=heater_width,
                length=heater_taper_length,
                cross_section=x,
            )
            taper1 = c << taper
            taper2 = c << taper
            taper1.connect("o1", via_stack_west.ports["e3"])
            taper2.connect("o1", via_stack_east.ports["e1"])

    c.info["resistance"] = (
        ohms_per_square * heater_width * length if ohms_per_square else None
    )
    return c


straight_heater_metal = gf.partial(
    straight_heater_metal_undercut,
    with_undercut=False,
)
straight_heater_metal_90_90 = gf.partial(
    straight_heater_metal_undercut,
    with_undercut=False,
    port_orientation1=90,
    port_orientation2=90,
)
straight_heater_metal_undercut_90_90 = gf.partial(
    straight_heater_metal_undercut,
    with_undercut=False,
    port_orientation1=90,
    port_orientation2=90,
)


def test_ports():
    c = straight_heater_metal(length=50.0)
    assert c.ports["o2"].center[0] == 50.0, c.ports["o2"].center[0]
    return c


if __name__ == "__main__":
    # c = test_ports()
    # c = straight_heater_metal_undercut()
    # print(c.ports['o2'].center[0])
    # c.pprint_ports()
    # c = straight_heater_metal(heater_width=5, length=50.0)

    c = straight_heater_metal(length=40)
    # n = c.get_netlist()
    # c.show(show_ports=True)
    scene = c.to_3d()
    scene.show()
