import datetime
import time
from typing import Tuple, TypeVar

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
        self._lines_widget = AttributedLinesWidget()
        super().__init__(self._lines_widget)

    def render(self, size: Tuple[int, int], focus: bool) -> None:
        width, height = size

        self._tree.render(width, height)
        self._lines_widget.set_lines(self._tree.lines)

        return super().render(size, focus)

    def selectable(self):
        return True

    def keypress(self, size: Tuple[int, int], key: str):
        if key == "shift up":
            self._tree.scroll(-1)
        elif key == "shift down":
            self._tree.scroll(1)
        elif key == "shift right":
            self._tree.scroll_horizontally(1)
        elif key == "shift left":
            self._tree.scroll_horizontally(-1)
        else:
            t = datetime.datetime(2019,5,7,13,25,6)
            self._tree._supply.add(Message(str(time.time()), None, t, "key", key))
            self._invalidate()
