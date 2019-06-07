# TODO retrieve attributes of any (x, y) coordinates
# TODO retrieve attributes of closest existing line (by y coordinate)

import collections
from typing import Deque, Iterator, List, Optional, Tuple

from .markup import AT, AttributedText, Attributes

__all__ = ["Line", "AttributedLines"]

Line = Tuple[Attributes, AttributedText]

class AttributedLines:
    """
    AttributedLines is a list of lines of AttributedText that maintains a
    vertical offset.

    When rendering a tree of messages, the RenderedMessage-s are drawn line by
    line to an AttributedLines. The AttributedLines is then displayed in an
    AttributedLinesWidget.

    Multiple AttributedLines can be concatenated, keeping either the first or
    the second AttributedLines's offset.
    """

    def __init__(self, lines: Optional[List[Line]] = None) -> None:
        self.upper_offset = 0
        self._lines: Deque[Line] = collections.deque(lines or [])

    def __iter__(self) -> Iterator[Line]:
        return self._lines.__iter__()

    def __len__(self) -> int:
        return len(self._lines)

    @property
    def lower_offset(self) -> int:
        # When there's one element in the list, the lower and upper offsets are
        # the same. From that follows that in an empty list, the lower offset
        # must be smaller than the upper offset.
        return self.upper_offset + (len(self) - 1)

    @lower_offset.setter
    def lower_offset(self, lower_offset: int) -> None:
        self.upper_offset = lower_offset - (len(self) - 1)

    # Modifying functions

    def append_above(self,
            attributes: Attributes,
            text: AttributedText) -> None:
        """
        Append a line above all already existing lines. The existing lines'
        offsets do not change.
        """

        self._lines.appendleft((attributes, text))
        self.upper_offset -= 1

    def append_below(self,
            attributes: Attributes,
            text: AttributedText) -> None:
        """
        Append a line below all already existing lines. The existing lines'
        offsets do not change.
        """

        self._lines.append((attributes, text))
        # lower offset does not need to be modified since it's calculated based
        # on the upper offset

    def extend_above(self, lines: "AttributedLines") -> None:
        """
        Prepend an AttributedLines, ignoring its offsets and using the current
        AttributedLines's offsets instead.
        """

        self._lines.extendleft(reversed(lines._lines))
        self.upper_offset -= len(lines)

    def extend_below(self, lines: "AttributedLines") -> None:
        """
        Append an AttributedLines, ignoring its offsets and using the current
        AttributedLines's offsets instead.
        """

        self._lines.extend(lines._lines)
        # lower offset does not need to be modified since it's calculated based
        # on the upper offset

    # Non-modifying functions

    def between(self, start_offset: int, end_offset: int) -> "AttributedLines":
        """
        Returns a new AttributedLines object containing only the lines between
        (and including) start_offset and end_offset.
        """

        lines = []

        for i, line in enumerate(self):
            line_offset = self.upper_offset + i
            if start_offset <= line_offset <= end_offset:
                lines.append(line)

        attr_lines = AttributedLines(lines)
        attr_lines.upper_offset = max(start_offset, self.upper_offset)
        attr_lines.lower_offset = min(end_offset, self.lower_offset)
        return attr_lines

    def to_size(self, start_offset: int, end_offset: int) -> "AttributedLines":
        """
        Same as between(), but fills the AttributedLines with empty lines where
        necessary so that the new upper_offset is the start_offset and the new
        lower_offset is the end_offset.
        """

        between = self.between(start_offset, end_offset)

        while between.upper_offset > start_offset:
            between.append_above({}, AT())

        while between.lower_offset < end_offset:
            between.append_below({}, AT())

        return between

    @staticmethod
    def render_line(
            line: Line,
            width: int,
            horizontal_offset: int,
            offset_char: str = " ",
            overlap_char: str = "…",
            ) -> AttributedText:
        """
        Renders a single line to a specified width with a specified horizontal
        offset, applying all line-wide attributes to the result. The length of
        the resulting line is exactly the specified width.

        The offset_char is used to pad the line if it is shorter than required.

        The overlap_char is used to mark the lines that extend beyond the right
        edge of the widget.
        """

        attributes, text = line
        # column to the right is reserved for the overlap char
        text_width = width - 1

        start_offset = horizontal_offset
        end_offset = start_offset + text_width

        result: AttributedText = AT()

        if start_offset < 0:
            pad_length = min(text_width, -start_offset)
            result += AT(offset_char * pad_length)

        if end_offset < 0:
            pass # the text should not be displayed at all
        elif end_offset < len(text):
            if start_offset > 0:
                result += text[start_offset:end_offset]
            else:
                result += text[:end_offset]
        else:
            if start_offset > 0:
                result += text[start_offset:]
            else:
                result += text

        if end_offset > len(text):
            pad_length = min(text_width, end_offset - len(text))
            result += AT(offset_char * pad_length)

        if end_offset < len(text):
            result += AT(overlap_char)
        else:
            result += AT(offset_char)

        for k, v in attributes.items():
            result = result.set(k, v)

        return result

    def render_lines(self,
            width: int,
            height: int,
            horizontal_offset: int,
            ) -> List[AttributedText]:
        """
        Renders all lines individually.
        """

        lines = []

        for line in self.to_size(0, height - 1):
            lines.append(self.render_line(line, width, horizontal_offset))

        return lines

    def render(self,
            width: int,
            height: int,
            horizontal_offset: int,
            ) -> AttributedText:
        """
        Renders all lines and combines them into a single AttributedText by
        joining them with a newline.
        """

        lines = self.render_lines(width, height,
                horizontal_offset=horizontal_offset)
        return AT("\n").join(lines)
