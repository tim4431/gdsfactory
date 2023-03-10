"""FileWatcher based on watchdog. Looks for changes in files with .pic.yml extension."""

from __future__ import annotations

import importlib
import logging
import pathlib
import sys
import time
import traceback
from typing import Callable, Optional

from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer

from gdsfactory.config import cwd
from gdsfactory.pdk import get_active_pdk


class YamlEventHandler(FileSystemEventHandler):
    """Captures pic.yml file change events."""

    def __init__(self, logger=None, path: Optional[str] = None):
        """Initialize the YAML event handler."""
        super().__init__()

        self.logger = logger or logging.root
        pdk = get_active_pdk()
        pdk.register_cells_yaml(dirpath=path, update=True)

    def update_cell(self, src_path, update: bool = False) -> Callable:
        """Parses a YAML file to a cell function and registers into active pdk.

        Args:
            src_path: the path to the file
            update: if True, will update an existing cell function of the same name without raising an error
        Returns:
            The cell function parsed from the yaml file.

        """
        from gdsfactory.cell import CACHE

        pdk = get_active_pdk()
        print(f"Active PDK: {pdk.name}")
        filepath = pathlib.Path(src_path)
        cell_name = filepath.stem.split(".")[0]
        if cell_name in CACHE:
            CACHE.pop(cell_name)
        parser = pdk.circuit_yaml_parser
        function = parser(filepath, name=cell_name)
        try:
            pdk.register_cells_yaml(**{cell_name: function}, update=update)
        except ValueError as e:
            print(e)
        return function

    def on_moved(self, event):
        super().on_moved(event)

        what = "directory" if event.is_directory else "file"
        if what == "file" and event.dest_path.endswith(".pic.yml"):
            self.logger.info("Moved %s: %s", what, event.src_path)
            self.update_cell(event.dest_path)
            self.get_component(event.src_path)

    def on_created(self, event):
        super().on_created(event)

        what = "directory" if event.is_directory else "file"
        if what == "file" and event.src_path.endswith(".pic.yml"):
            self.logger.info("Created %s: %s", what, event.src_path)
            self.update_cell(event.src_path)
            self.get_component(event.src_path)

    def on_deleted(self, event):
        super().on_deleted(event)

        what = "directory" if event.is_directory else "file"

        if what == "file" and event.src_path.endswith(".pic.yml"):
            self.logger.info("Deleted %s: %s", what, event.src_path)
            pdk = get_active_pdk()
            filepath = pathlib.Path(event.src_path)
            cell_name = filepath.stem.split(".")[0]
            pdk.remove_cell(cell_name)

    def on_modified(self, event):
        super().on_modified(event)

        what = "directory" if event.is_directory else "file"
        if (
            what == "file"
            and event.src_path.endswith(".pic.yml")
            or event.src_path.endswith(".py")
        ):
            self.logger.info("Modified %s: %s", what, event.src_path)
            self.get_component(event.src_path)

    def get_component(self, filepath):
        try:
            filepath = pathlib.Path(filepath)
            if filepath.exists():
                if str(filepath).endswith(".pic.yml"):
                    cell_func = self.update_cell(filepath, update=True)
                    c = cell_func()
                    c.show(show_ports=True)
                    # on_yaml_cell_modified.fire(c)
                    return c
                elif str(filepath).endswith(".py"):
                    d = dict(locals(), **globals())
                    d.update(__name__="__main__")
                    exec(filepath.read_text(), d, d)
                else:
                    print("Changed file {filepath} ignored (not .pic.yml or .py)")

        except Exception as e:
            traceback.print_exc(file=sys.stdout)
            print(e)


def watch(path=cwd, pdk=None) -> None:
    path = str(path)
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    if pdk:
        pdk_module = importlib.import_module(pdk)
        pdk_module.PDK.activate()
    event_handler = YamlEventHandler(path=path)
    observer = Observer()
    observer.schedule(event_handler, path, recursive=True)
    observer.start()
    logging.info(f"Observing {path!r}")
    try:
        while True:
            time.sleep(1)
    finally:
        observer.stop()
        observer.join()


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "."
    watch(path)
