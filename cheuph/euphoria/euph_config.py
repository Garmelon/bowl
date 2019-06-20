from typing import Any, Dict, List, Optional, TypeVar

from ..config import (ConfigValueException, Kind, Option, TransparentConfig,
                      TreeLoader)

__all__ = ["EuphConfig", "EuphLoader"]

class EuphConfig(TransparentConfig):

    def __init__(self, parent: Optional[TransparentConfig] = None) -> None:
        super().__init__(parent)

    @property
    def room_style(self) -> str:
        return self["visual.room_style"]

    @property
    def nick_style(self) -> str:
        return self["visual.nick_style"]

    @property
    def own_nick_style(self) -> str:
        return self["visual.own_nick_style"]

    @property
    def error_style(self) -> str:
        return self["visual.error.style"]

    @property
    def error_room_style(self) -> str:
        return self["visual.error.room_style"]

    # meta

    @property
    def show_year(self) -> bool:
        return self["visual.meta.show_year"]

    @property
    def show_seconds(self) -> bool:
        return self["visual.meta.show_seconds"]

    @property
    def meta_style(self) -> str:
        return self["visual.meta.style"]

    # surround

    @property
    def surround_left(self) -> str:
        return self["visual.surround.left"]

    @property
    def surround_right(self) -> str:
        return self["visual.surround.right"]

    @property
    def surround_style(self) -> str:
        return self["visual.surround.style"]

    # cursor

    @property
    def cursor_surround_left(self) -> str:
        return self["visual.cursor.surround.left"]

    @property
    def cursor_surround_right(self) -> str:
        return self["visual.cursor.surround.right"]

    @property
    def cursor_surround_style(self) -> str:
        return self["visual.cursor.surround.style"]

    @property
    def cursor_own_nick_style(self) -> str:
        return self["visual.cursor.own_nick_style"]

    @property
    def cursor_fill_char(self) -> str:
        return self["visual.cursor.fill.char"]

    @property
    def cursor_fill_style(self) -> str:
        return self["visual.cursor.fill.style"]

    @property
    def palette(self) -> Any:
        return self["palette"]

class EuphLoader(TreeLoader):

    DEFAULT_STYLES = {
            "none": {},
            "bold": {"fg": "bold"},
            "gray": {"fg": "dark gray"},

            "room": {"fg": "bold, light blue"},
            "nick": {"fg": "light cyan"},
            "own_nick": {"fg": "yellow"},

            "error": {"fg": "light red"},
            "error_room": {"fg": "bold, yellow"},
    }

    # Various conditions
    SINGLE_CHAR = (lambda x: len(x) == 1, "must be single character")

    def __init__(self) -> None:
        super().__init__()

        self._styles: Set[str] = set()

        self.add_style("visual.room_style", "room")
        self.add_style("visual.nick_style", "nick")
        self.add_style("visual.own_nick_style", "own_nick")

        self.add_style("visual.error.style", "error")
        self.add_style("visual.error.room_style", "error_room")

        # meta
        self.add("visual.meta.show_year", Kind.BOOL, False)
        self.add("visual.meta.show_seconds", Kind.BOOL, False)
        self.add_style("visual.meta.style", "none")

        # surround
        self.add("visual.surround.left", Kind.STR, "[", [self.SINGLE_CHAR])
        self.add("visual.surround.right", Kind.STR, "]", [self.SINGLE_CHAR])
        self.add_style("visual.surround.style", "none")

        # cursor
        self.add("visual.cursor.surround.left", Kind.STR, "<", [self.SINGLE_CHAR])
        self.add("visual.cursor.surround.right", Kind.STR, ">", [self.SINGLE_CHAR])
        self.add_style("visual.cursor.surround.style", "none")
        self.add_style("visual.cursor.own_nick_style", "own_nick")
        self.add("visual.cursor.fill.char", Kind.STR, " ", [self.SINGLE_CHAR])
        self.add_style("visual.cursor.fill.style", "none")

        self.add("styles", Kind.DICT, self.DEFAULT_STYLES)

    def add_style(self, name: str, default: str) -> None:
        self.add(name, Kind.STR, default)
        self._styles.add(name)

    def load_to(self, config: TransparentConfig, data: Any) -> None:
        super().load_to(config, data)

        styles = self._get_styles(config)
        self._check_style_properties(config, styles)
        config["palette"] = self._load_palette(styles)

    def _get_styles(self, config: TransparentConfig) -> Dict[str, Dict[str, str]]:
        # First, collect all the styles from front to back
        style_list = []
        current_config: Optional[TransparentConfig] = config
        while current_config is not None:
            try:
                style_list.append(current_config.get("styles"))
            except ConfigValueException:
                pass

            current_config = current_config.parent

        # Then, mush them together in reverse order
        styles: Dict[str, Dict[str, str]] = {}
        for style in reversed(style_list):
            if type(style) is not dict:
                raise ConfigValueException("invalid styles format")

            for name, info in style.items():
                if type(name) is not str:
                    raise ConfigValueException(
                        f"style {name!r} has to be named with a string")

                if info is None:
                    styles[name] = {}
                    continue

                if type(info) is not dict:
                    raise ConfigValueException(
                            f"style {name!r} has an incorrect value")

                for key, value in info.items():
                    if type(key) is not str or type(value) is not str:
                        raise ConfigValueException(
                                f"style {name!r} has an incorrect value")

                styles[name] = info

        return styles

    def _load_palette(self, styles: Dict[str, Dict[str, str]]) -> List[Any]:
        palette: List[Any] = []

        for style, info in styles.items():
            keys = set(info.keys())

            if keys == {"alias"}:
                palette.append((style, info["alias"]))
            elif keys.issubset({"fg", "bg"}):
                fg = info.get("fg", "")
                bg = info.get("bg", "")
                palette.append((style, fg, bg))
            else:
                raise ConfigValueException(f"style {style} has an incorrect format")

        return palette

    def _check_style_properties(self,
            config: TransparentConfig,
            styles: Dict[str, Dict[str, str]],
            ) -> None:

        for name in self._styles:
            style_name = config.get(name)
            if style_name not in styles:
                raise ConfigValueException((f"style {style_name!r} is not"
                        " specified in the styles section"))
