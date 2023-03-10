from __future__ import annotations

from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import numpy as np

import gdsfactory as gf
from gdsfactory.component import Component, ComponentReference
from gdsfactory.port import Port, flipped
from gdsfactory.routing.get_route import get_route
from gdsfactory.typings import Route


def sort_key_west_to_east(port: Port) -> float:
    return port.x


def sort_key_east_to_west(port: Port) -> float:
    return -port.x


def sort_key_south_to_north(port: Port) -> float:
    return port.y


def sort_key_north_to_south(port: Port) -> float:
    return -port.y


def route_ports_to_side(
    ports: Union[Dict[str, Port], List[Port], Component, ComponentReference],
    side: str = "north",
    x: Optional[float] = None,
    y: Optional[float] = None,
    routing_func=get_route,
    **kwargs,
) -> Tuple[List[Route], List[Port]]:
    """Routes ports to a given side.

    Args:
        ports: list/dict/Component/ComponentReference to route to a side.
        side: 'north', 'south', 'east' or 'west'.
        x: position to route ports for east/west. None, uses most east/west value.
        y: position to route ports for south/north. None, uses most north/south value.
        routing_func: the routing function. By default uses `get_route`.

    Keyword Args:
      radius: in um.
      separation: in um.
      extend_bottom/extend_top for east/west routing.
      extend_left, extend_right for south/north routing.

    Returns:
        List of routes: with routing elements.
        List of ports: of the new ports.

    .. plot::
        :include-source:

        import gdsfactory as gf

        c = gf.Component('sample_route_sides')
        dummy = gf.components.nxn(north=2, south=2, west=2, east=2)
        sides = ["north", "south", "east", "west"]
        d = 100
        positions = [(0, 0), (d, 0), (d, d), (0, d)]

        for pos, side in zip(positions, sides):
            dummy_ref = dummy.ref(position=pos)
            c.add(dummy_ref)
            routes, ports = gf.routing.route_ports_to_side(dummy_ref, side, layer=(1, 0))
            for route in routes:
                c.add(route.references)
            for i, p in enumerate(ports):
                c.add_port(name=f"{side[0]}{i}", port=p)

        c.plot()

    """
    if not ports:
        return [], []

    # Accept list of ports, Component or dict of ports
    if isinstance(ports, dict):
        ports = list(ports.values())

    elif isinstance(ports, (Component, ComponentReference)):
        ports = list(ports.ports.values())

    # Choose which
    if side in {"north", "south"}:
        func_route = route_ports_to_y
        xy = y if y is not None else side
    elif side in {"west", "east"}:
        xy = x if x is not None else side
        func_route = route_ports_to_x
    else:
        raise ValueError(f"side = {side} not valid (north, south, west, east)")

    return func_route(ports, xy, routing_func=routing_func, **kwargs)


def route_ports_to_north(list_ports, **kwargs):
    return route_ports_to_side(list_ports, side="north", **kwargs)


def route_ports_to_south(list_ports, **kwargs):
    return route_ports_to_side(list_ports, side="south", **kwargs)


def route_ports_to_west(list_ports, **kwargs):
    return route_ports_to_side(list_ports, side="west", **kwargs)


def route_ports_to_east(list_ports, **kwargs):
    return route_ports_to_side(list_ports, side="east", **kwargs)


def route_ports_to_x(
    list_ports: List[Port],
    x: Union[float, str] = "east",
    separation: float = 10.0,
    radius: float = 10.0,
    extend_bottom: float = 0.0,
    extend_top: float = 0.0,
    extension_length: float = 0.0,
    y0_bottom: Optional[float] = None,
    y0_top: Optional[float] = None,
    routing_func: Callable = get_route,
    backward_port_side_split_index: int = 0,
    start_straight_length: float = 0.01,
    dx_start: Optional[float] = None,
    dy_start: Optional[float] = None,
    **routing_func_args,
) -> Tuple[List[Route], List[Port]]:
    """Returns route to x.

    Args:
        list_ports: reasonably well behaved list of ports.
           ports facing north ports are norther than any other ports
           ports facing south ports are souther ...
           ports facing west ports are the wester ...
           ports facing east ports are the easter ...
        x: float or string.
           if float: x coordinate to which the ports will be routed
           if string: "east" -> route to east
           if string: "west" -> route to west
        separation: in um.
        radius: in um.
        extend_bottom: in um.
        extend_top: in um.
        extension_length: in um.
        y0_bottom: in um.
        y0_top: in um.
        routing_func: to route.
        backward_port_side_split_index: integer represents and index in the list of backwards ports (bottom to top)
                all ports with an index strictly lower or equal are routed bottom
            all ports with an index larger or equal are routed top
        dx_start: override minimum starting x distance.
        dy_start: override minimum starting y distance.

    Returns:
        routes: list of routes
        ports: list of the new optical ports

    1. routes the bottom-half of the ports facing opposite side of x
    2. routes the south ports
    3. front ports
    4. north ports

    """
    north_ports = [p for p in list_ports if p.orientation == 90]
    south_ports = [p for p in list_ports if p.orientation == 270]
    east_ports = [p for p in list_ports if p.orientation == 0]
    west_ports = [p for p in list_ports if p.orientation == 180]

    epsilon = 1.0
    a = epsilon + max(radius, separation)
    bx = epsilon + max(radius, dx_start) if dx_start else a
    by = epsilon + max(radius, dy_start) if dy_start else a

    xs = [p.x for p in list_ports]
    ys = [p.y for p in list_ports]

    if y0_bottom is None:
        y0_bottom = min(ys) - by

    y0_bottom -= extend_bottom

    if y0_top is None:
        y0_top = max(ys) + (max(radius, dy_start) if dy_start else a)
    y0_top += extend_top

    if x == "west" and extension_length > 0:
        extension_length = -extension_length

    if x == "east":
        x = max(p.x for p in list_ports) + bx
    elif x == "west":
        x = min(p.x for p in list_ports) - bx
    elif isinstance(x, (float, int)):
        pass
    else:
        raise ValueError(f"x={x!r} should be a float or east or west")

    if x < min(xs):
        sort_key_north = sort_key_west_to_east
        sort_key_south = sort_key_west_to_east
        forward_ports = west_ports
        backward_ports = east_ports
        angle = 0

    elif x > max(xs):
        sort_key_south = sort_key_east_to_west
        sort_key_north = sort_key_east_to_west
        forward_ports = east_ports
        backward_ports = west_ports
        angle = 180
    else:
        raise ValueError("x should be either to the east or to the west of all ports")

    # forward_ports.sort()
    north_ports.sort(key=sort_key_north)
    south_ports.sort(key=sort_key_south)
    forward_ports.sort(key=sort_key_south_to_north)

    backward_ports.sort(key=sort_key_south_to_north)
    backward_ports_thru_south = backward_ports[:backward_port_side_split_index]
    backward_ports_thru_north = backward_ports[backward_port_side_split_index:]
    backward_ports_thru_south.sort(key=sort_key_south_to_north)
    backward_ports_thru_north.sort(key=sort_key_north_to_south)

    routes = []
    ports = []

    def add_port(
        p, y, l_elements, l_ports, start_straight_length=start_straight_length
    ) -> None:
        new_port = p.copy(name=f"{p.name}_new")
        new_port.orientation = angle
        new_port.center = (x + extension_length, y)
        l_elements += [
            routing_func(
                p,
                new_port,
                start_straight_length=start_straight_length,
                radius=radius,
                **routing_func_args,
            )
        ]
        l_ports += [new_port.flip()]

    y_optical_bot = y0_bottom
    for p in south_ports:
        add_port(p, y_optical_bot, routes, ports)
        y_optical_bot -= separation

    for p in forward_ports:
        add_port(p, p.y, routes, ports)

    y_optical_top = y0_top
    for p in north_ports:
        add_port(p, y_optical_top, routes, ports)
        y_optical_top += separation

    start_straight_length_section = start_straight_length
    max_x = max(xs)
    min_x = min(xs)

    for p in backward_ports_thru_north:
        # Extend ports if necessary
        if angle == 0 and p.x < max_x:
            start_straight_length_section = max_x - p.x
        elif angle == 180 and p.x > min_x:
            start_straight_length_section = p.x - min_x
        else:
            start_straight_length_section = 0

        add_port(
            p,
            y_optical_top,
            routes,
            ports,
            start_straight_length=start_straight_length + start_straight_length_section,
        )
        y_optical_top += separation
        start_straight_length += separation

    start_straight_length_section = start_straight_length
    for p in backward_ports_thru_south:
        # Extend ports if necessary
        if angle == 0 and p.x < max_x:
            start_straight_length_section = max_x - p.x
        elif angle == 180 and p.x > min_x:
            start_straight_length_section = p.x - min_x
        else:
            start_straight_length_section = 0

        add_port(
            p,
            y_optical_bot,
            routes,
            ports,
            start_straight_length=start_straight_length + start_straight_length_section,
        )
        y_optical_bot -= separation
        start_straight_length += separation

    return routes, ports


def route_ports_to_y(
    list_ports: List[Port],
    y: Union[float, str] = "north",
    separation: float = 10.0,
    radius: float = 10.0,
    x0_left: Optional[float] = None,
    x0_right: Optional[float] = None,
    extension_length: float = 0.0,
    extend_left: float = 0.0,
    extend_right: float = 0.0,
    routing_func: Callable = get_route,
    backward_port_side_split_index: int = 0,
    start_straight_length: float = 0.01,
    dx_start: float = None,
    dy_start: float = None,
    **routing_func_args: Dict[Any, Any],
) -> Tuple[List[Route], List[Port]]:
    """Args are the following.

        list_ports: reasonably well behaved list of ports.
           ports facing north ports are norther than any other ports
           ports facing south ports are souther ...
           ports facing west ports are the wester ...
           ports facing east ports are the easter ...

        y: float or string.
               if float: y coordinate to which the ports will be routed
               if string: "north" -> route to north
               if string: "south" -> route to south

        backward_port_side_split_index: integer
               this integer represents and index in the list of backwards ports
                   (sorted from left to right)
               all ports with an index strictly larger are routed right
               all ports with an index lower or equal are routed left
        separation: in um.
        radius: in um.

    Returns:
        - a list of Routes
        - a list of the new optical ports

    First route the bottom-half of the back ports
        (back ports are the one facing opposite side of x)
    Then route the south ports
    then the front ports
    then the north ports
    """
    if y == "south" and extension_length > 0:
        extension_length = -extension_length

    da = 45
    north_ports = [
        p for p in list_ports if p.orientation > 90 - da and p.orientation < 90 + da
    ]
    south_ports = [
        p for p in list_ports if p.orientation > 270 - da and p.orientation < 270 + da
    ]
    east_ports = [
        p for p in list_ports if p.orientation < da or p.orientation > 360 - da
    ]
    west_ports = [
        p for p in list_ports if p.orientation < 180 + da and p.orientation > 180 - da
    ]

    epsilon = 1.0
    a = radius + max(radius, separation)
    bx = epsilon + max(radius, dx_start) if dx_start else a
    by = epsilon + max(radius, dy_start) if dy_start else a

    xs = [p.x for p in list_ports]
    ys = [p.y for p in list_ports]

    if x0_left is None:
        x0_left = min(xs) - bx
    x0_left -= extend_left

    if x0_right is None:
        x0_right = max(xs) + (max(radius, dx_start) if dx_start else a)
    x0_right += extend_right

    if y == "north":
        y = (
            max(
                p.y + a * np.abs(np.cos(p.orientation * np.pi / 180))
                for p in list_ports
            )
            + by
        )
    elif y == "south":
        y = (
            min(
                p.y - a * np.abs(np.cos(p.orientation * np.pi / 180))
                for p in list_ports
            )
            - by
        )
    elif isinstance(y, (float, int)):
        pass
    if y <= min(ys):
        sort_key_east = sort_key_south_to_north
        sort_key_west = sort_key_south_to_north
        forward_ports = south_ports
        backward_ports = north_ports
        angle = 90.0

    elif y >= max(ys):
        sort_key_west = sort_key_north_to_south
        sort_key_east = sort_key_north_to_south
        forward_ports = north_ports
        backward_ports = south_ports
        angle = -90.0
    else:
        raise ValueError("y should be either to the north or to the south of all ports")

    west_ports.sort(key=sort_key_west)
    east_ports.sort(key=sort_key_east)
    forward_ports.sort(key=sort_key_west_to_east)
    backward_ports.sort(key=sort_key_east_to_west)

    backward_ports.sort(key=sort_key_west_to_east)
    backward_ports_thru_west = backward_ports[:backward_port_side_split_index]
    backward_ports_thru_east = backward_ports[backward_port_side_split_index:]

    backward_ports_thru_west.sort(key=sort_key_west_to_east)
    backward_ports_thru_east.sort(key=sort_key_east_to_west)

    routes = []
    ports = []

    def add_port(
        p, x, l_elements, l_ports, start_straight_length=start_straight_length
    ):
        new_port = p.copy()
        new_port.orientation = angle
        new_port.center = (x, y + extension_length)

        if np.sum(np.abs((new_port.center - p.center) ** 2)) < 1e-12:
            l_ports += [flipped(new_port)]
            return

        try:
            l_elements += [
                routing_func(
                    p,
                    new_port,
                    start_straight_length=start_straight_length,
                    radius=radius,
                    **routing_func_args,
                )
            ]
            l_ports += [flipped(new_port)]

        except Exception as error:
            raise ValueError(
                f"Could not connect {p.name!r} to {new_port.name!r}"
            ) from error

    x_optical_left = x0_left
    for p in west_ports:
        add_port(p, x_optical_left, routes, ports)
        x_optical_left -= separation

    for p in forward_ports:
        add_port(p, p.x, routes, ports)

    x_optical_right = x0_right
    for p in east_ports:
        add_port(p, x_optical_right, routes, ports)
        x_optical_right += separation

    start_straight_length_section = start_straight_length
    for p in backward_ports_thru_east:
        add_port(
            p,
            x_optical_right,
            routes,
            ports,
            start_straight_length=start_straight_length_section,
        )
        x_optical_right += separation
        start_straight_length_section += separation

    start_straight_length_section = start_straight_length
    for p in backward_ports_thru_west:
        add_port(
            p,
            x_optical_left,
            routes,
            ports,
            start_straight_length=start_straight_length_section,
        )
        x_optical_left -= separation
        start_straight_length_section += separation

    return routes, ports


@gf.cell
def _sample_route_side() -> Component:
    c = Component()
    xs = [0.0, 10.0, 25.0, 50.0]
    ys = [0.0, 10.0, 25.0, 50.0]
    a = 5
    xl = min(xs) - a
    xr = max(xs) + a
    yb = min(ys) - a
    yt = max(ys) + a

    layer = (1, 0)

    c.add_polygon([(xl, yb), (xl, yt), (xr, yt), (xr, yb)], layer)

    for i, y in enumerate(ys):
        p0 = (xl, y)
        p1 = (xr, y)
        c.add_port(name=f"W{i}", center=p0, orientation=180, width=0.5, layer=layer)
        c.add_port(name=f"E{i}", center=p1, orientation=0, width=0.5, layer=layer)

    for i, x in enumerate(xs):
        p0 = (x, yb)
        p1 = (x, yt)
        c.add_port(name=f"S{i}", center=p0, orientation=270, width=0.5, layer=layer)
        c.add_port(name=f"N{i}", center=p1, orientation=90, width=0.5, layer=layer)

    return c


@gf.cell
def _sample_route_sides() -> Component:
    c = Component()
    dummy = _sample_route_side()
    sides = ["north", "south", "east", "west"]
    positions = [(0, 0), (400, 0), (400, 400), (0, 400)]
    for pos, side in zip(positions, sides):
        dummy_ref = dummy.ref(position=pos)
        c.add(dummy_ref)
        routes, ports = route_ports_to_side(dummy_ref, side, layer=(1, 0))
        for route in routes:
            c.add(route.references)
        for i, p in enumerate(ports):
            c.add_port(name=f"{side[0]}{i}", port=p)
    return c


if __name__ == "__main__":
    c = Component("sample_route_sides")
    dummy = gf.components.nxn(north=2, south=2, west=2, east=2)
    sides = ["north", "south", "east", "west"]
    d = 100
    positions = [(0, 0), (d, 0), (d, d), (0, d)]

    for pos, side in zip(positions, sides):
        dummy_ref = dummy.ref(position=pos)
        c.add(dummy_ref)
        routes, ports = route_ports_to_side(dummy_ref, side, layer=(1, 0))
        for route in routes:
            c.add(route.references)
        for i, p in enumerate(ports):
            c.add_port(name=f"{side[0]}{i}", port=p)

    # c.plot()
    c.show(show_ports=True)
