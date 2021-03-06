from typing import Any, List, Tuple, Union

import urwid

from .markup import AT

__all__ = ["AttributedTextWidget", "ATWidget"]

class AttributedTextWidget(urwid.Text):
    """
    A widget that works like urwid.Text, but displays AttributedText.

    The AttributedText's "style" attribute is used as the style for urwid.Text,
    where present.
    """

    def __init__(self,
            text: AT,
            *args: Any,
            **kwargs: Any,
            ) -> None:
        """
        text - an AttributedText object

        All other arguments are passed onto a urwid.Text constructor and thus
        work the same way.
        """

        self._attributed_text = text
        super().__init__(self._convert_to_markup(text), *args, **kwargs)

    @staticmethod
    def _convert_to_markup(text: AT) -> List[Union[str, Tuple[str, str]]]:
        # Wonder why mypy can't figure out the type signature of markup on its
        # own... :P
        markup: List[Union[str, Tuple[str, str]]]
        markup = [
                segment.text if style is None else (style, segment.text)
                for segment, style in text.split_by("style")
        ]

        return markup or [""]

    def set_attributed_text(self, text: AT) -> None:
        """
        Set the content of the AttributedTextWidget.
        """

        self._attributed_text = text
        super().set_text(self._convert_to_markup(text))

    def get_attributed_text(self) -> AT:
        """
        Returns the currently used AttributedText.

        urwid.Text's get_text() also returns a run length encoded list of
        attributes. This is not necessary here because the AttributedText
        already contains all its attributes.
        """

        return self._attributed_text

    @property
    def attributed_text(self) -> AT:
        return self.get_attributed_text()

ATWidget = AttributedTextWidget
