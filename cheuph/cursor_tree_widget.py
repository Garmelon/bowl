# TODO remove testing code and clean up

import datetime
import time
from typing import Optional, Tuple, TypeVar

import urwid

from .attributed_lines_widget import AttributedLinesWidget
from .cursor_rendering import CursorTreeRenderer
from .element import Element, Message

__all__ = ["CursorTreeWidget"]

E = TypeVar("E", bound=Element)

class CursorTreeWidget(urwid.WidgetWrap):
    """
    This widget draws a CursorTree and moves the cursor around.
    """

    def __init__(self, tree: CursorTreeRenderer[E]) -> None:
        self._tree = tree
        self._lines = AttributedLinesWidget()
        super().__init__(self._lines)

        self._tree._cursor_id = "->3->2->3"

    def render(self, size: Tuple[int, int], focus: bool) -> None:
        width, height = size

        self._tree.render(width, height)
        self._lines.set_lines(self._tree.lines)

        return super().render(size, focus)

    def selectable(self) -> bool:
        return True

    def keypress(self, size: Tuple[int, int], key: str) -> Optional[str]:
        if key == "shift up":
            self._tree.scroll(1)
            self._invalidate()
        elif key == "shift down":
            self._tree.scroll(-1)
            self._invalidate()
        elif key == "shift right":
            self.scroll_horizontally(1)
        elif key == "shift left":
            self.scroll_horizontally(-1)
        elif key in {"home", "shift home"}:
            self._lines.horizontal_offset = 0
            self._invalidate()
        else:
            t = datetime.datetime(2019,5,7,13,25,6)
            self._tree._supply.add(Message(
                str(time.time()),
                self._tree._cursor_id,
                t,
                "key",
                key,
            ))
            self._invalidate()

        return None

    def scroll_horizontally(self, offset: int) -> None:
        self._lines.horizontal_offset = max(0,
                self._lines.horizontal_offset + offset)
        self._invalidate()
