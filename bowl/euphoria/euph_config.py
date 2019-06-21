from typing import Any, Dict, List, Optional, Set

from ..config import ConfigValueException, Kind, TransparentConfig, TreeLoader

__all__ = ["EuphConfig", "EuphLoader"]

class EuphConfig(TransparentConfig):

    def __init__(self, parent: Optional[TransparentConfig] = None) -> None:
        super().__init__(parent)

    # basic styles

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

    # indent

    @property
    def indent_width(self) -> int:
        return self["visual.indent.width"]

    @property
    def indent_char(self) -> str:
        return self["visual.indent.char"]

    @property
    def indent_fill(self) -> str:
        return self["visual.indent.fill"]

    @property
    def indent_style(self) -> str:
        return self["visual.indent.style"]

    # cursor

    @property
    def cursor_own_nick_style(self) -> str:
        return self["visual.cursor.own_nick_style"]

    @property
    def cursor_fill_char(self) -> str:
        return self["visual.cursor.fill.char"]

    @property
    def cursor_fill_style(self) -> str:
        return self["visual.cursor.fill.style"]

    # cursor.surround

    @property
    def cursor_surround_left(self) -> str:
        return self["visual.cursor.surround.left"]

    @property
    def cursor_surround_right(self) -> str:
        return self["visual.cursor.surround.right"]

    @property
    def cursor_surround_style(self) -> str:
        return self["visual.cursor.surround.style"]

    # cursor.indent

    @property
    def indent_cursor_char(self) -> str:
        return self["visual.cursor.indent.char"]

    @property
    def indent_cursor_corner(self) -> str:
        return self["visual.cursor.indent.corner"]

    @property
    def indent_cursor_fill(self) -> str:
        return self["visual.cursor.indent.fill"]

    @property
    def indent_cursor_style(self) -> str:
        return self["visual.cursor.indent.style"]

    # scroll

    @property
    def scrolloff(self) -> int:
        return self["visual.scroll.scrolloff"]

    @property
    def vertical_scroll(self) -> int:
        return self["visual.scroll.vertical"]

    @property
    def horizontal_scroll(self) -> int:
        return self["visual.scroll.horizontal"]

    @property
    def half_page_scroll(self) -> bool:
        return self["visual.scroll.half_page"]

    # borders

    @property
    def room_name_separator(self) -> str:
        return self["visual.borders.room_name_separator"]

    @property
    def room_name_split(self) -> str:
        return self["visual.borders.room_name_split"]

    @property
    def nick_list_separator(self) -> str:
        return self["visual.borders.nick_list_separator"]

    @property
    def nick_list_split(self) -> str:
        return self["visual.borders.nick_list_split"]

    @property
    def edit_separator(self) -> str:
        return self["visual.borders.edit_separator"]

    @property
    def borders_style(self) -> str:
        return self["visual.borders.style"]

    # other

    @property
    def palette(self) -> Any:
        return self["palette"]

class EuphLoader(TreeLoader):

    DEFAULT_STYLES = {
            "none": {},
            "bold": {"fg": "bold"},
            "gray": {"fg": "dark gray"},

            "cursor": {"fg": "bold, light green"},

            "room": {"fg": "bold, light blue"},
            "nick": {"fg": "light cyan"},
            "own_nick": {"fg": "yellow"},

            "error": {"fg": "light red"},
            "error_room": {"fg": "bold, yellow"},
    }

    # Various conditions
    SINGLE_CHAR = (lambda x: len(x) == 1, "must be single character")
    AT_LEAST_0 = (lambda x: x >= 0, "must be at least 0")
    AT_LEAST_1 = (lambda x: x >= 1, "must be at least 1")

    def __init__(self) -> None:
        super().__init__()

        self._styles: Set[str] = set()

        # basic styles
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
        self.add("visual.surround.left", Kind.STR, "[", self.SINGLE_CHAR)
        self.add("visual.surround.right", Kind.STR, "]", self.SINGLE_CHAR)
        self.add_style("visual.surround.style", "bold")

        # indent
        self.add("visual.indent.width", Kind.INT, 2, self.AT_LEAST_1)
        self.add("visual.indent.char", Kind.STR, "│", self.SINGLE_CHAR)
        self.add("visual.indent.fill", Kind.STR, " ", self.SINGLE_CHAR)
        self.add_style("visual.indent.style", "gray")

        # cursor
        self.add_style("visual.cursor.own_nick_style", "cursor")
        self.add("visual.cursor.fill.char", Kind.STR, " ", self.SINGLE_CHAR)
        self.add_style("visual.cursor.fill.style", "none")

        # cursor.surround
        self.add("visual.cursor.surround.left", Kind.STR, "<",
                self.SINGLE_CHAR)
        self.add("visual.cursor.surround.right", Kind.STR, ">",
                self.SINGLE_CHAR)
        self.add_style("visual.cursor.surround.style", "cursor")

        # cursor.indent
        self.add("visual.cursor.indent.char", Kind.STR, "┃", self.SINGLE_CHAR)
        self.add("visual.cursor.indent.corner", Kind.STR, "┗",
                self.SINGLE_CHAR)
        self.add("visual.cursor.indent.fill", Kind.STR, "━", self.SINGLE_CHAR)
        self.add_style("visual.cursor.indent.style", "cursor")

        # scroll
        self.add("visual.scroll.scrolloff", Kind.INT, 3, self.AT_LEAST_0)
        self.add("visual.scroll.vertical", Kind.INT, 2, self.AT_LEAST_1)
        self.add("visual.scroll.horizontal", Kind.INT, 8, self.AT_LEAST_1)
        self.add("visual.scroll.half_page", Kind.BOOL, True)

        # borders
        self.add("visual.borders.room_name_separator", Kind.STR, "═",
                self.SINGLE_CHAR)
        self.add("visual.borders.room_name_split", Kind.STR, "╤",
                self.SINGLE_CHAR)
        self.add("visual.borders.nick_list_separator", Kind.STR, "│",
                self.SINGLE_CHAR)
        self.add("visual.borders.nick_list_split", Kind.STR, "┤",
                self.SINGLE_CHAR)
        self.add("visual.borders.edit_separator", Kind.STR, "─",
                self.SINGLE_CHAR)
        self.add_style("visual.borders.style", "gray")

        # other
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
