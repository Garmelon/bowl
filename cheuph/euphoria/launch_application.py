import argparse
import asyncio
import logging
import pathlib
from typing import Any, Callable, Optional

import urwid
import yaml

from .euph_config import EuphConfig, EuphLoader

__all__ = ["DEFAULT_CONFIG_PATHS", "launch"]

DEFAULT_CONFIG_PATHS = [
        "~/.config/cheuph/cheuph.yaml",
        "~/.cheuph/cheuph.yaml",
        "~/.cheuph.yaml",
]

GITHUB_URL = "https://github.com/Garmelon/cheuph"

def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
            description="A terminal-based client for euphoria.io",
            epilog=f"For more information, see {GITHUB_URL}",
            )
    parser.add_argument("-e", "--export-defaults", type=str)
    parser.add_argument("-c", "--config-file", type=str)
    return parser.parse_args()

def load_config_yaml(args: argparse.Namespace) -> Optional[str]:
    path = None # TODO get from args
    if path is None:
        paths = DEFAULT_CONFIG_PATHS
    else:
        paths = [path]

    for raw_path in paths:
        path = pathlib.Path(raw_path).expanduser()
        try:
            with open(path) as f:
                return yaml.load(f.read(), Loader=yaml.SafeLoader)
        except FileNotFoundError:
            print(f"Could not load config from {path}")

    print("Could not find a config file. Using default settings.")
    input("Press enter to continue") # TODO use better prompt?
    return None

def load_config(args: Any) -> EuphConfig:
    loader = EuphLoader()
    defaults = loader.defaults()
    config = EuphConfig(defaults)

    config_yaml = load_config_yaml(args) or {}
    loader.load_to(config, config_yaml)

    return config

def export_defaults(path: str) -> None:
    path = pathlib.Path(path).expanduser()
    print(f"Exporting default config to {path}")

    loader = EuphLoader()
    defaults = loader.export(loader.defaults())
    dumped = yaml.dump(
            defaults,
            Dumper=yaml.SafeDumper,
            allow_unicode=True,
    )

    with open(path, "w") as f:
        f.write(dumped)

def launch(
        application: Callable[[EuphConfig], urwid.Widget],
        ) -> None:

    logging.disable(logging.CRITICAL)

    args = parse_arguments()

    if args.export_defaults is not None:
        export_defaults(args.export_defaults)
        return

    config = load_config(args)
    loop = asyncio.get_event_loop()

    main_loop = urwid.MainLoop(
            application(config),
            event_loop=urwid.AsyncioEventLoop(loop=loop),
            palette=config.palette,
    )

    main_loop.run()
