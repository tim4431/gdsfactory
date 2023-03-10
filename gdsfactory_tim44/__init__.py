"""You can import gdsfactory.as gf.

functions:
    - import_gds(): returns a Component from a GDS

classes:

    - Component
    - Port
    - TECH

modules:

    - c: components
    - routing

isort:skip_file
"""
from __future__ import annotations
from warnings import warn
from functools import partial
from toolz import compose
from gdsfactory.component_layout import Group
from gdsfactory.path import Path


# NOTE: import order matters. Only change the order if you know what you are doing
from gdsfactory.component import Component, ComponentReference
from gdsfactory.config import CONF, call_if_func, PATH
from gdsfactory.port import Port
from gdsfactory.cell import cell
from gdsfactory.cell import cell_without_validator
from gdsfactory.cell import clear_cache
from gdsfactory.show import show
from gdsfactory.read.import_gds import import_gds
from gdsfactory.cross_section import CrossSection, Section
from gdsfactory.component_layout import Label
from gdsfactory import decorators
from gdsfactory import cross_section
from gdsfactory import labels
from gdsfactory import asserts
from gdsfactory import components
from gdsfactory import routing
from gdsfactory import typings
from gdsfactory import path
from gdsfactory import snap
from gdsfactory import read
from gdsfactory import add_termination
from gdsfactory import functions
from gdsfactory import geometry
from gdsfactory import add_ports
from gdsfactory import write_cells
from gdsfactory import add_pins
from gdsfactory import technology
from gdsfactory import fill

from gdsfactory.add_tapers import add_tapers
from gdsfactory.add_padding import (
    add_padding,
    add_padding_container,
    get_padding_points,
)
from gdsfactory.fill import fill_rectangle
from gdsfactory.pack import pack
from gdsfactory.grid import grid, grid_with_text
from gdsfactory.generic_tech import LAYER, LAYER_STACK, get_generic_pdk
from gdsfactory.pdk import (
    Pdk,
    get_component,
    get_cross_section,
    get_layer,
    get_active_pdk,
    get_cell,
    get_constant,
)
from gdsfactory.get_factories import get_cells
from gdsfactory.cross_section import get_cross_section_factories

c = components


def __getattr__(name):
    if name == "types":
        warn("gdsfactory.types has been renamed to gdsfactory.typings")
        return typings
    raise AttributeError(f"No module named {name}")


__all__ = (
    "CONF",
    "Component",
    "ComponentReference",
    "CrossSection",
    "Group",
    "LAYER",
    "LAYER_STACK",
    "Label",
    "Path",
    "Pdk",
    "Port",
    "Section",
    "add_padding",
    "add_padding_container",
    "add_pins",
    "add_ports",
    "add_tapers",
    "add_termination",
    "asserts",
    "c",
    "call_if_func",
    "cell",
    "cell_without_validator",
    "clear_cache",
    "components",
    "compose",
    "cross_section",
    "decorators",
    "fill",
    "fill_rectangle",
    "functions",
    "geometry",
    "get_active_pdk",
    "get_cell",
    "get_cells",
    "get_component",
    "get_constant",
    "get_cross_section",
    "get_cross_section_factories",
    "get_layer",
    "get_padding_points",
    "get_generic_pdk",
    "grid",
    "grid_with_text",
    "import_gds",
    "labels",
    "pack",
    "partial",
    "path",
    "read",
    "routing",
    "show",
    "snap",
    "typings",
    "technology",
    "write_cells",
    "PATH",
)
__version__ = "6.56.0"
