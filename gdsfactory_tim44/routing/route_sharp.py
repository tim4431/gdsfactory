"""based on phidl.routing."""
from __future__ import annotations

from typing import Optional, Tuple

import numpy as np

import gdsfactory as gf
from gdsfactory.component import Component
from gdsfactory.cross_section import CrossSection
from gdsfactory.path import Path, transition
from gdsfactory.port import Port
from gdsfactory.routing.route_quad import _get_rotated_basis
from gdsfactory.typings import CrossSectionSpec, LayerSpec


def path_straight(port1: Port, port2: Port) -> Path:
    """Return waypoint path between port1 and port2 in a straight line.

    Useful when ports point directly at each other.

    Args:
        port1: start port.
        port2: end port.

    """
    delta_orientation = np.round(
        np.abs(np.mod(port1.orientation - port2.orientation, 360)), 3
    )
    e1, e2 = _get_rotated_basis(port1.orientation)
    displacement = port2.center - port1.center
    xrel = np.round(
        np.dot(displacement, e1), 3
    )  # relative position of port 2, forward/backward
    yrel = np.round(
        np.dot(displacement, e2), 3
    )  # relative position of port 2, left/right
    if (delta_orientation not in (0, 180, 360)) or (yrel != 0) or (xrel <= 0):
        raise ValueError("path_straight(): ports must point directly at each other.")
    return Path(np.array([port1.center, port2.center]))


def path_L(port1: Port, port2: Port) -> Path:
    """Return waypoint path between port1 and port2 in an L shape.

    Useful when orthogonal ports can be directly connected with one turn.

    Args:
        port1: start port.
        port2: end port.

    """
    delta_orientation = np.round(
        np.abs(np.mod(port1.orientation - port2.orientation, 360)), 3
    )
    if delta_orientation not in (90, 270):
        raise ValueError("path_L(): ports must be orthogonal.")
    e1, e2 = _get_rotated_basis(port1.orientation)
    # assemble waypoints
    pt1 = port1.center
    pt3 = port2.center
    delta_vec = pt3 - pt1
    pt2 = pt1 + np.dot(delta_vec, e1) * e1
    return Path(np.array([pt1, pt2, pt3]))


def path_U(port1: Port, port2: Port, length1=200) -> Path:
    """Return waypoint path between port1 and port2 in a U shape. Useful when ports face the same direction or toward each other.

    Args:
        port1: start port.
        port2: end port.
        length1: Length of segment exiting port1.
            Should be larger than bend radius.

    """
    delta_orientation = np.round(
        np.abs(np.mod(port1.orientation - port2.orientation, 360)), 3
    )
    if delta_orientation not in (0, 180, 360):
        raise ValueError("path_U(): ports must be parallel.")
    theta = np.radians(port1.orientation)
    e1 = np.array([np.cos(theta), np.sin(theta)])
    e2 = np.array([-1 * np.sin(theta), np.cos(theta)])
    # assemble waypoints
    pt1 = port1.center
    pt4 = port2.center
    pt2 = pt1 + length1 * e1  # outward by length1 distance
    delta_vec = pt4 - pt2
    pt3 = pt2 + np.dot(delta_vec, e2) * e2
    return Path(np.array([pt1, pt2, pt3, pt4]))


def path_J(port1: Port, port2: Port, length1=200, length2=200) -> Path:
    """Return waypoint path between port1 and port2 in a J shape. Useful when \
    orthogonal ports cannot be connected directly with an L shape.

    Args:
        port1: start port.
        port2: end port.
        length1: Length of segment exiting port1.
            Should be larger than bend radius.
        length2: Length of segment exiting port2.
            Should be larger than bend radius.

    """
    delta_orientation = np.round(
        np.abs(np.mod(port1.orientation - port2.orientation, 360)), 3
    )
    if delta_orientation not in (90, 270):
        raise ValueError("path_J(): ports must be orthogonal.")
    e1, _ = _get_rotated_basis(port1.orientation)
    e2, _ = _get_rotated_basis(port2.orientation)
    # assemble waypoints
    pt1 = port1.center
    pt2 = pt1 + length1 * e1  # outward from port1 by length1
    pt5 = port2.center
    pt4 = pt5 + length2 * e2  # outward from port2 by length2
    delta_vec = pt4 - pt2
    pt3 = pt2 + np.dot(delta_vec, e2) * e2  # move orthogonally in e2 direction
    return Path(np.array([pt1, pt2, pt3, pt4, pt5]))


def path_C(port1: Port, port2: Port, length1=100, left1=100, length2=100) -> Path:
    """Return waypoint path between port1 and port2 in a C shape. Useful when ports are parallel and face away from each other.

    Args:
        port1: start port.
        port2: end port.
        length1: Length of route segment coming out of port1. Should be at larger
            than bend radius.
        left1: Length of route segment that turns left (or right if negative)
            from port1. Should be larger than twice the bend radius.
        length2: Length of route segment coming out of port2. Should be larger
            than bend radius.

    """
    delta_orientation = np.round(
        np.abs(np.mod(port1.orientation - port2.orientation, 360)), 3
    )
    if delta_orientation not in (0, 180, 360):
        raise ValueError("path_C(): ports must be parallel.")
    e1, e_left = _get_rotated_basis(port1.orientation)
    e2, _ = _get_rotated_basis(port2.orientation)
    # assemble route points
    pt1 = port1.center
    pt2 = pt1 + length1 * e1  # outward from port1 by length1
    pt3 = pt2 + left1 * e_left  # leftward by left1
    pt6 = port2.center
    pt5 = pt6 + length2 * e2  # outward from port2 by length2
    delta_vec = pt5 - pt3
    pt4 = pt3 + np.dot(delta_vec, e1) * e1  # move orthogonally in e1 direction
    return Path(np.array([pt1, pt2, pt3, pt4, pt5, pt6]))


def path_manhattan(port1: Port, port2: Port, radius) -> Path:
    """Return waypoint path between port1 and port2 using manhattan routing. Routing is performed using straight, L, U, J, or C  waypoint path as needed. Ports must face orthogonal or parallel directions.

    Args:
        port1: start port.
        port2: end port.
        radius: Bend radius for 90 degree bend.

    """
    radius = radius + 0.1  # ensure space for bend radius
    e1, e2 = _get_rotated_basis(port1.orientation)
    displacement = port2.center - port1.center
    xrel = np.round(
        np.dot(displacement, e1), 3
    )  # port2 position, forward(+)/backward(-) from port 1
    yrel = np.round(
        np.dot(displacement, e2), 3
    )  # port2 position, left(+)/right(-) from port1
    orel = np.round(
        np.abs(np.mod(port2.orientation - port1.orientation, 360)), 3
    )  # relative orientation
    if orel not in (0, 90, 180, 270, 360):
        raise ValueError(
            "path_manhattan(): ports must face parallel or orthogonal directions."
        )
    if orel in (90, 270):
        # Orthogonal case
        if (
            (orel == 90 and yrel < -1 * radius) or (orel == 270 and yrel > radius)
        ) and xrel > radius:
            pts = path_L(port1, port2)
        else:
            # Adjust length1 and length2 to ensure intermediate segments fit bend radius
            direction = -1 if (orel == 270) else 1
            length2 = (
                2 * radius - direction * yrel
                if (np.abs(radius + direction * yrel) < 2 * radius)
                else radius
            )
            length1 = (
                2 * radius + xrel if (np.abs(radius - xrel) < 2 * radius) else radius
            )
            pts = path_J(port1, port2, length1=length1, length2=length2)
    elif orel == 180 and yrel == 0 and xrel > 0:
        pts = path_straight(port1, port2)
    elif (orel == 180 and xrel <= 2 * radius) or (np.abs(yrel) < 2 * radius):
        # Adjust length1 and left1 to ensure intermediate segments fit bend radius
        left1 = np.abs(yrel) + 2 * radius if (np.abs(yrel) < 4 * radius) else 2 * radius
        y_direction = -1 if (yrel < 0) else 1
        left1 = y_direction * left1
        length2 = radius
        x_direction = -1 if (orel == 180) else 1
        segmentx_length = np.abs(xrel + x_direction * length2 - radius)
        length1 = (
            xrel + x_direction * length2 + 2 * radius
            if segmentx_length < 2 * radius
            else radius
        )

        pts = path_C(port1, port2, length1=length1, length2=length2, left1=left1)
    else:
        # Adjust length1 to ensure segment comes out of port2
        length1 = radius + xrel if (orel == 0 and xrel > 0) else radius
        pts = path_U(port1, port2, length1=length1)
    return pts


def path_Z(port1: Port, port2: Port, length1=100, length2=100) -> Path:
    """Return waypoint path between port1 and port2 in a Z shape. Ports can \
    have any relative orientation.

    Args:
        port1: start port.
        port2: end port.
        length1: Length of route segment coming out of port1.
        length2: Length of route segment coming out of port2.

    """
    # get basis vectors in port directions
    e1, _ = _get_rotated_basis(port1.orientation)
    e2, _ = _get_rotated_basis(port2.orientation)
    # assemble route  points
    pt1 = port1.center
    pt2 = pt1 + length1 * e1  # outward from port1 by length1
    pt4 = port2.center
    pt3 = pt4 + length2 * e2  # outward from port2 by length2
    return Path(np.array([pt1, pt2, pt3, pt4]))


def path_V(port1: Port, port2: Port) -> Path:
    """Return waypoint path between port1 and port2 in a V shape. Useful when \
    ports point to a single connecting point.

    Args:
        port1: start port.
        port2: end port.

    """
    # get basis vectors in port directions
    e1, _ = _get_rotated_basis(port1.orientation)
    e2, _ = _get_rotated_basis(port2.orientation)

    # assemble route  points
    pt1 = port1.center
    pt3 = port2.center

    # solve for intersection
    E = np.column_stack((e1, -1 * e2))
    pt2 = np.matmul(np.linalg.inv(E), pt3 - pt1)[0] * e1 + pt1
    return Path(np.array([pt1, pt2, pt3]))


@gf.cell
def route_sharp(
    port1: Port,
    port2: Port,
    width: Optional[float] = None,
    path_type: str = "manhattan",
    manual_path=None,
    layer: Optional[LayerSpec] = None,
    cross_section: Optional[CrossSectionSpec] = None,
    port_names: Tuple[str, str] = ("o1", "o2"),
    **kwargs,
) -> Component:
    """Returns Component route between ports.

    Args:
        port1: start port.
        port2: end port.
        width: None, int, float, array-like[2], or CrossSection.
            If None, the route linearly tapers between the widths the ports
            If set to a single number (e.g. `width=1.7`): makes a fixed-width route
            If set to a 2-element array (e.g. `width=[1.8,2.5]`): makes a route
                whose width varies linearly from width[0] to width[1]
            If set to a CrossSection: uses the CrossSection parameters for the route.
        path_type : {'manhattan', 'L', 'U', 'J', 'C', 'V', 'Z', 'straight', 'manual'}.
        manual_path: array-like[N][2] or Path Waypoint for  manual route.
        layer: Layer to put route on.
        kwargs: Keyword arguments passed to the waypoint path function.

        Method of waypoint path creation. Should be one of
        - manhattan: automatic manhattan routing (see path_manhattan() ).
        - L: L-shaped path for orthogonal ports that can be directly connected.
        - U: U-shaped path for parallel or facing ports.
        - J: J-shaped path for orthogonal ports that cannot be directly connected.
        - C: C-shaped path for ports that face away from each other.
        - Z: Z-shaped path with three segments for ports at any angles.
        - V: V-shaped path with two segments for ports at any angles.
        - straight: straight path for ports that face each other.
        - manual: use an explicit waypoint path provided in manual_path.

    .. plot::
        :include-source:

        import gdsfactory as gf

        c = gf.Component("pads")
        c1 = c << gf.components.pad(port_orientation=None)
        c2 = c << gf.components.pad(port_orientation=None)

        c2.movex(400)
        c2.movey(-200)

        route = c << gf.routing.route_sharp(c1.ports["e4"], c2.ports["e1"], path_type="L")
        c.plot()

    """
    if path_type == "C":
        P = path_C(port1, port2, **kwargs)
    elif path_type == "J":
        P = path_J(port1, port2, **kwargs)
    elif path_type == "L":
        P = path_L(port1, port2)
    elif path_type == "U":
        P = path_U(port1, port2, **kwargs)
    elif path_type == "V":
        P = path_V(port1, port2)
    elif path_type == "Z":
        P = path_Z(port1, port2, **kwargs)
    elif path_type == "manhattan":
        radius = max(port1.width, port2.width)
        P = path_manhattan(port1, port2, radius=radius)
    elif path_type == "manual":
        P = manual_path if isinstance(manual_path, Path) else Path(manual_path)
    elif path_type == "straight":
        P = path_straight(port1, port2)
    else:
        raise ValueError(
            f"route_sharp() received invalid path_type {path_type} not in "
            "{'manhattan', 'L', 'U', 'J', 'C', 'V', 'Z', 'straight', 'manual'}"
        )

    if cross_section:
        cross_section = gf.get_cross_section(cross_section)
        D = P.extrude(cross_section=cross_section)
    elif width is None:
        layer = layer or port1.layer
        X1 = CrossSection(
            width=port1.width, port_names=port_names, layer=layer, name="x1"
        )
        X2 = CrossSection(
            width=port2.width, port_names=port_names, layer=layer, name="x2"
        )
        cross_section = transition(
            cross_section1=X1, cross_section2=X2, width_type="linear"
        )
        D = P.extrude(cross_section=cross_section)
    else:
        D = P.extrude(width=width, layer=layer)
        if not isinstance(width, CrossSection):
            newport1 = D.add_port(port=port1, name=1).rotate(180)
            newport2 = D.add_port(port=port2, name=2).rotate(180)
            if np.size(width) == 1:
                newport1.width = width
                newport2.width = width
            if np.size(width) == 2:
                newport1.width = width[0]
                newport2.width = width[1]
    return D


if __name__ == "__main__":
    c = gf.Component("pads")
    c1 = c << gf.components.pad(port_orientation=None)
    c2 = c << gf.components.pad(port_orientation=None)

    c2.movex(400)
    c2.movey(-200)

    route = c << route_sharp(c1.ports["e4"], c2.ports["e1"], path_type="L")
    c.show(show_ports=True)
