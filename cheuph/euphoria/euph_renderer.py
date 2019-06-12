import unicodedata

from ..cursor_rendering import CursorRenderer
from ..element import Message, RenderedMessage
from ..markup import AT, AttributedText, Attributes

__all__ = ["EuphRenderer"]

class EuphRenderer(CursorRenderer):

    YEAR_FORMAT = "%y-%m-%d "
    YEAR_WIDTH = 11

    TIME_FORMAT = "%H:%M"
    TIME_WIDTH = 5

    SECOND_FORMAT = ":%S"
    SECOND_WIDTH = 3

    NORMAL_WIDTH = {"N", "Na", "H", "A"}

    def __init__(self,
            nick: str,
            replace_wide_unicode: bool = True,
            unicode_placeholder: str = "�",
            # Meta settings
            show_year: bool = False,
            show_seconds: bool = False,
            meta_attrs: Attributes = {},
            # Surround settings
            surround_left: str = "[",
            surround_right: str = "]",
            surround_attrs: Attributes = {},
            # Cursor settings
            cursor_surround_left: str = "<",
            cursor_surround_right: str = ">",
            cursor_surround_attrs: Attributes = {},
            cursor_own_nick_attrs: Attributes = {},
            cursor_fill: str = " ",
            cursor_fill_attrs: Attributes = {},
            # Various attributes
            nick_attrs: Attributes = {},
            own_nick_attrs: Attributes = {},
            ) -> None:

        self.nick = nick
        self._replace_wide_unicode = replace_wide_unicode
        self._unicode_placeholder = unicode_placeholder
        # Meta settings
        self._show_year = show_year
        self._show_seconds = show_seconds
        self._meta_attrs = meta_attrs
        # Surround settings
        self._surround_left = surround_left
        self._surround_right = surround_right
        self._surround_attrs = surround_attrs
        # Cursor settings
        self._cursor_surround_left = cursor_surround_left
        self._cursor_surround_right = cursor_surround_right
        self._cursor_surround_attrs = cursor_surround_attrs
        self._cursor_own_nick_attrs = cursor_own_nick_attrs
        self._cursor_fill = cursor_fill
        self._cursor_fill_attrs = cursor_fill_attrs
        # Various attributes
        self._nick_attrs = nick_attrs
        self._own_nick_attrs = own_nick_attrs

    @property
    def meta_width(self) -> int:
        width = self.TIME_WIDTH + 1 # One space at the end

        if self._show_year:
            width += self.YEAR_WIDTH

        if self._show_seconds:
            width += self.SECOND_WIDTH

        return width

    def _filter_unicode(self, text: str) -> str:
        if not self._replace_wide_unicode:
            return text

        new_chars = []
        for char in text:
            if unicodedata.east_asian_width(char) in self.NORMAL_WIDTH:
                new_chars.append(char)
            else:
                new_chars.append(self._unicode_placeholder)

        return "".join(new_chars)

    def _render_meta(self, message: Message) -> AttributedText:
        elements = [self.TIME_FORMAT]

        if self._show_year:
            elements.insert(0, self.YEAR_FORMAT)

        if self._show_seconds:
            elements.append(self.SECOND_FORMAT)

        text = message.timestamp.strftime("".join(elements))
        return AT(text, attributes=self._meta_attrs) + AT(" ")

    def render_element(self, message: Message, width: int) -> RenderedMessage:
        meta = self._render_meta(message)

        left = AT(self._surround_left, attributes=self._surround_attrs)
        nick = AT(self._filter_unicode(message.nick),
                attributes=self._nick_attrs) # TODO detect own nick
        right = AT(self._surround_right, attributes=self._surround_attrs)

        nick_str = left + nick + right + AT(" ")
        nick_spaces = AT(" " * len(nick))

        content = self._filter_unicode(message.content)
        lines = []
        for i, line in enumerate(content.split("\n")):
            text = (nick_str if i == 0 else nick_spaces) + AT(line)
            lines.append(text)

        return RenderedMessage(message.id, lines, meta)

    def render_cursor(self, width: int) -> AttributedText:
        left = AT(self._cursor_surround_left,
                attributes=self._cursor_surround_attrs)
        nick = AT(self._filter_unicode(self.nick),
                attributes=self._cursor_own_nick_attrs)
        right = AT(self._cursor_surround_right,
                attributes=self._cursor_surround_attrs)

        nick_str = left + nick + right

        rest_width = max(0, width - len(nick_str))
        rest_str = AT(self._cursor_fill * rest_width,
                attributes=self._cursor_fill_attrs)

        return nick_str + rest_str
