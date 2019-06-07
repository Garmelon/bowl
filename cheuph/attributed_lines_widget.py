# TODO send event on mouse click

from typing import Optional, Tuple

import urwid

from .attributed_lines import AttributedLines
from .attributed_text_widget import AttributedTextWidget
from .markup import AT

__all__ = ["AttributedLinesWidget"]

class AttributedLinesWidget(urwid.WidgetWrap):
    """
    This widget draws an AttributedLines with a horizontal and a vertical
    offset.
    """

    def __init__(self, lines: Optional[AttributedLines] = None) -> None:
        self._text = AttributedTextWidget(AT())
        self._filler = urwid.Filler(self._text, valign=urwid.TOP)
        super().__init__(self._filler)

        self._horizontal_offset = 0

        self.set_lines(lines or AttributedLines())

    @property
    def horizontal_offset(self) -> int:
        return self._horizontal_offset

    @horizontal_offset.setter
    def horizontal_offset(self, offset: int) -> None:
        if offset != self._horizontal_offset:
            self._horizontal_offset = offset
            self._invalidate()

    @property
    def upper_offset(self) -> int:
        return self._lines.upper_offset

    @upper_offset.setter
    def upper_offset(self, offset: int) -> None:
        self._lines.upper_offset = offset
        self._invalidate()

    @property
    def lower_offset(self) -> int:
        return self._lines.lower_offset

    @lower_offset.setter
    def lower_offset(self, offset: int) -> None:
        self._lines.lower_offset = offset
        self._invalidate()

    def set_lines(self, lines: AttributedLines) -> None:
        self._lines = lines
        self._invalidate()

    def render(self, size: Tuple[int, int], focus: bool) -> None:
        width, height = size

        text = self._lines.render(width, height, self.horizontal_offset)
        self._text.set_attributed_text(text)

        return super().render(size, focus)
