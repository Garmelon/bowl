from typing import Any, Optional, Tuple

import urwid

from .attributed_lines import AttributedLines
from .attributed_text_widget import AttributedTextWidget
from .markup import AT, AttributedText, Attributes

__all__ = ["AttributedLinesWidget"]


class AttributedLinesWidget(urwid.WidgetWrap):
    """
    This widget draws lines of AttributedText with a horizontal and a vertical
    offset. It can retrieve the attributes of any character by its (x, y)
    coordinates. Line-wide attributes may be specified.

    When clicked, it sends an event containing the attributes of the character
    that was just clicked.

    Uses the following config values:
    - "filler_symbol"
    - "overflow_symbol"
    """

    def __init__(self,
            lines: Optional[AttributedLines] = None,
            ) -> None:

        self._horizontal_offset = 0

        self._text = AttributedTextWidget(AT())
        self._filler = urwid.Filler(self._text, valign=urwid.TOP)
        super().__init__(self._filler)

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
