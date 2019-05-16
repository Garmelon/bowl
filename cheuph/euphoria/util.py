from typing import List, Tuple, Union

from ..config import Config

__all__ = ["UtilException","Palette", "palette_from_config", "DEFAULT_CONFIG"]

class UtilException(Exception):
    pass

Palette = List[Union[Tuple[str, str], Tuple[str, str, str],
    Tuple[str, str, str, str]]]

def palette_from_config(conf: Config) -> Palette:
    palette: Palette = []

    styles = conf.tree["style"]
    for style, info in styles.items():
        # First, do the alias stuff
        alias = info.get("alias")
        if isinstance(alias, str):
            if alias in styles:
                palette.append((style, alias))
                continue
            else:
                raise UtilException((f"style.{style}.alias must be the name of"
                    " another style"))
        elif alias is not None:
            raise UtilException(f"style.{style}.alias must be a string")

        # Foreground/background
        fg = info.get("fg")
        bg = info.get("bg")

        if not isinstance(fg, str) and fg is not None:
            raise TypeError(f"style.{style}.fg must be a string")

        if not isinstance(bg, str) and bg is not None:
            raise TypeError(f"style.{style}.bg must be a string")

        fg = fg or ""
        bg = bg or ""

        palette.append((style, fg, bg))

    return palette

DEFAULT_CONFIG = {
    "element": {
        "room": "room",
    },
    "style": {
        "room": {
            "fg": "light blue, bold",
        },
    },
}
