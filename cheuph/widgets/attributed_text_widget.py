from typing import Any

import urwid

from ..markup import AttributedText

__all__ = ["AttributedTextWidget", "ATWidget"]

class AttributedTextWidget(urwid.Text):
    """
    A widget that works like urwid.Text, but displays AttributedText.

    The AttributedText's "style" attribute is used as the style for urwid.Text,
    where present.
    """

    def __init__(self,
            text: AttributedText,
            *args: Any,
            **kwargs: Any
            ) -> None:
        """
        text - an AttributedText object

        All other arguments are passed onto a urwid.Text constructor and thus
        work the same way.
        """

        chunk_info = [
                chunk.text if style is None else (style, chunk.text)
                for chunk, style in text.split_by("style")
        ]
        super().__init__(chunk_info, *args, **kwargs)

ATWidget = AttributedTextWidget
