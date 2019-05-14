from typing import Any, FrozenSet

import urwid

from ..element_supply import ElementSupply
from ..markup import AT
from ..tree_display import TreeDisplay
from .attributed_text_widget import AttributedTextWidget

__all__ = ["TreeDisplayWidget"]

class TreeDisplayWidget(urwid.WidgetWrap):
    def __init__(self, supply: ElementSupply) -> None:
        self._display = TreeDisplay(supply, 80, 50)

        self._sizing = frozenset({"box"})
        self._selectable = False

        # I could set wrap="clip", but the TreeDisplay should already cut its
        # display_lines to the correct width, based on its size. Leaving the
        # wrap on might help with users spotting things going wrong.
        self._text_widget = AttributedTextWidget(AT())

        super().__init__(urwid.Filler(self._text_widget))

    @property
    def display(self) -> TreeDisplay:
        return self._display

    def render(self, size: Any, focus: Any) -> Any:
        self._display.width, self._display.height = size
        self._display.rerender()
        self._display.render_display_lines()

        text = AT("\n").join(self._display.display_lines)
        self._text_widget.set_attributed_text(text)

        return self._w.render(size, focus)
