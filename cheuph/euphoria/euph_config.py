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
    def error_style(self) -> str:
        return self["visual.error.style"]

    @property
    def error_room_style(self) -> str:
        return self["visual.error.room_style"]

    @property
    def palette(self) -> Any:
        return self["palette"]

class EuphLoader(TreeLoader):

    STYLE_PROPERTIES = [
            "visual.room_style",
            "visual.error.style",
            "visual.error.room_style",
    ]

    DEFAULT_STYLES = {
            "room": {"fg": "bold, light blue"},
            "error": {"fg": "light red"},
            "error_room": {"fg": "bold, yellow"},
    }

    def __init__(self) -> None:
        super().__init__()

        self.add_option("visual.room_style", Option(Kind.STR, "room"))
        self.add_option("visual.error.style", Option(Kind.STR, "error"))
        self.add_option("visual.error.room_style", Option(Kind.STR, "error_room"))
        self.add_option("styles", Option(Kind.DICT, self.DEFAULT_STYLES))

    def load_to(self, config: TransparentConfig, data: Any) -> None:
        super().load_to(config, data)

        styles = self._get_styles(config)
        self._check_style_properties(config, styles)
        config["palette"] = self._load_palette(styles)

    def _get_styles(self, config: TransparentConfig) -> Dict[str, Dict[str, str]]:
        # First, collect all the styles from front to back
        style_list = []
        current_config = config
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

        for name in self.STYLE_PROPERTIES:
            style_name = config.get(name)
            if style_name not in styles:
                raise ConfigValueException((f"style {style_name!r} is not"
                        " specified in the styles section"))
