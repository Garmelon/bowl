from typing import Optional, Tuple, TypeVar

import urwid

from .attributed_lines_widget import AttributedLinesWidget
from .cursor_rendering import CursorTreeRenderer
from .element import Element

__all__ = ["CursorTreeWidget"]

E = TypeVar("E", bound=Element)

class CursorTreeWidget(urwid.WidgetWrap):
    """
    This widget draws a CursorTree and moves the cursor around.
    """

    def __init__(self,
            tree: CursorTreeRenderer[E],
            vertical_scroll_step: int = 1,
            horizontal_scroll_step: int = 4,
            half_page_scroll: bool = False,
            ) -> None:

        self._tree = tree
        self._lines = AttributedLinesWidget()

        super().__init__(self._lines)

        # Configurable variables
        if vertical_scroll_step < 1:
            raise ValueError("vertical scroll step must be at least 1")
        if horizontal_scroll_step < 1:
            raise ValueError("horizontal scroll step must be at least 1")
        self._vertical_scroll_step = vertical_scroll_step
        self._horizontal_scroll_step = horizontal_scroll_step
        self._half_page_scroll = half_page_scroll

    def render(self, size: Tuple[int, int], focus: bool) -> None:
        width, height = size

        self._tree.render(width, height)
        self._lines.set_lines(self._tree.lines)

        return super().render(size, focus)

    def selectable(self) -> bool:
        return True

    def keypress(self, size: Tuple[int, int], key: str) -> Optional[str]:
        width, height = size

        if key in {"up", "k"}:
            self._tree.move_cursor_up()
            self._invalidate()
        elif key in {"down", "j"}:
            self._tree.move_cursor_down()
            self._invalidate()
        elif key in {"shift up", "K"}:
            self._tree.scroll(self._vertical_scroll_step)
            self._invalidate()
        elif key in {"shift down", "J"}:
            self._tree.scroll(-self._vertical_scroll_step)
            self._invalidate()
        elif key in {"shift right", "L"}:
            self.scroll_horizontally(self._horizontal_scroll_step)
        elif key in {"shift left", "H"}:
            self.scroll_horizontally(-self._horizontal_scroll_step)
        elif key == "shift home":
            self._lines.horizontal_offset = 0
            self._invalidate()
        elif key == "shift page up":
            if self._half_page_scroll:
                self._tree.scroll(height // 2)
            else:
                self._tree.scroll(height - 1)
            self._invalidate()
        elif key == "shift page down":
            if self._half_page_scroll:
                self._tree.scroll(-(height // 2))
            else:
                self._tree.scroll(-(height - 1))
            self._invalidate()
        else:
            return key

        return None

    def scroll_horizontally(self, offset: int) -> None:
        self._lines.horizontal_offset = max(0,
                self._lines.horizontal_offset + offset)
        self._invalidate()
