# TODO move meta spaces rendering to message

from abc import ABC, abstractmethod
from typing import Generic, List, Optional, Tuple, TypeVar

from .attributed_lines import AttributedLines
from .element import Element, Id, Message, RenderedElement, RenderedMessage
from .element_supply import ElementSupply
from .exceptions import ShouldNeverHappen
from .markup import AT, AttributedText, Attributes
from .rendered_element_cache import RenderedElementCache

__all__ = ["CursorRenderer", "CursorTreeRenderer", "BasicCursorRenderer"]

E = TypeVar("E", bound=Element)
R = TypeVar("R", bound=RenderedElement)
M = TypeVar("M", bound=RenderedMessage) # because it has a meta field

class CursorRenderer(ABC, Generic[E, R]):

    @property
    @abstractmethod
    def meta_width(self) -> int:
        pass

    @abstractmethod
    def render_element(self, element: E, width: int) -> R:
        pass

    @abstractmethod
    def render_cursor(self, width: int) -> AttributedText:
        pass

class CursorTreeRenderer(Generic[E]):
    """
    This class renders a tree of Element-s from an ElementSupply to
    AttributedLines, including user interface elements like a cursor (and
    possibly subtree folding?).

    It does the following:
    1. render the tree
    2. handle scrolling
    3. handle the cursor
    """

    def __init__(self,
            supply: ElementSupply[E],
            renderer: CursorRenderer[E, M],
            indent_width: int = 2,
            indent: str = "│",
            indent_fill: str = " ",
            indent_attrs: Attributes = {},
            cursor_indent: str = "┃",
            cursor_corner: str = "┗",
            cursor_fill: str = "━",
            cursor_indent_attrs: Attributes = {},
            scrolloff: int = 3,
            ) -> None:

        self._supply = supply
        self._renderer = renderer
        self._cache = RenderedElementCache[M]()

        # Rendering result
        self._lines = AttributedLines()
        self._hit_top = False

        # Cursor and scrolling
        self._cursor_id: Optional[Id] = None
        self._anchor_id: Optional[Id] = None
        self._anchor_offset = 0.5

        # Last known dimensions
        self._width = 80
        self._height = 40

        # Configurable variables
        if indent_width < 0:
            raise ValueError("indent width must be 0 or greater")
        if scrolloff < 0:
            raise ValueError("scrolloff must be 0 or greater")
        self._indent_width = indent_width
        self._indent = indent
        self._indent_fill = indent_fill
        self._indent_attrs = indent_attrs
        self._cursor_indent = cursor_indent
        self._cursor_corner = cursor_corner
        self._cursor_fill = cursor_fill
        self._cursor_indent_attrs = cursor_indent_attrs
        self._scrolloff = scrolloff

    @property
    def lines(self) -> AttributedLines:
        # Not sure if the between() is necessary
        return self._lines.between(0, self._height - 1)

    @property
    def hit_top(self) -> bool:
        return self._hit_top

    # Offsets

    @staticmethod
    def get_absolute_offset(offset: float, height: int) -> int:
        return round(offset * (height - 1))

    @staticmethod
    def get_relative_offset(line: int, height: int) -> float:
        if height <= 1:
            return 0.5

        return line / (height - 1)

    @property
    def _absolute_anchor_offset(self) -> int:
        return self.get_absolute_offset(self._anchor_offset, self._height)

    @_absolute_anchor_offset.setter
    def _absolute_anchor_offset(self, offset: int) -> None:
        self._anchor_offset = self.get_relative_offset(offset, self._height)

    # Message cache operations

    def invalidate(self, message_id: Id) -> None:
        self._cache.invalidate(message_id)

    def invalidate_all(self) -> None:
        self._cache.invalidate_all()

    # Rendering a single message

    def _get_rendered_message(self, message_id: Id, width: int) -> M:
        cached = self._cache.get(message_id)
        if cached is not None:
            return cached

        message = self._supply.get(message_id)
        rendered = self._renderer.render_element(message, width)
        self._cache.add(rendered)
        return rendered

    def _render_message(self,
            message_id: Id,
            indent: AttributedText,
            ) -> AttributedLines:

        width = self._width - len(indent) - self._renderer.meta_width
        rendered: RenderedMessage = self._get_rendered_message(message_id,
                width)

        meta = rendered.meta
        meta_spaces = AT(" " * len(meta))

        lines = AttributedLines()
        for offset, line in enumerate(rendered.lines):
            text = (meta if offset == 0 else meta_spaces) + indent + line
            attrs = {"mid": message_id, "offset": offset}
            lines.append_below(attrs, text)

        return lines

    def _render_cursor(self,
            indent: AttributedText = AT(),
            ) -> AttributedLines:
        lines = AttributedLines()
        width = self._width - len(indent) - self._renderer.meta_width
        meta_spaces = AT(" " * self._renderer.meta_width)
        attrs = {"cursor": True, "offset": 0}
        lines.append_below(attrs, meta_spaces + indent +
                self._renderer.render_cursor(width))
        return lines

    def _render_indent(self,
            cursor: bool = False,
            cursor_line: bool = False,
            ) -> AttributedText:

        if self._indent_width < 1:
            return AT()

        if cursor_line:
            attrs = self._cursor_indent_attrs
            start = AT(self._cursor_corner, attributes=attrs)
            fill = AT(self._cursor_fill, attributes=attrs)
        elif cursor:
            start_attrs = self._cursor_indent_attrs
            start = AT(self._cursor_indent, attributes=start_attrs)
            fill_attrs = self._indent_attrs
            fill = AT(self._indent_fill, attributes=fill_attrs)
        else:
            attrs = self._indent_attrs
            start = AT(self._indent, attributes=attrs)
            fill = AT(self._indent_fill, attributes=attrs)

        return start + fill * (self._indent_width - len(start))

    # Rendering the tree

    def _render_subtree(self,
            lines: AttributedLines,
            root_id: Id,
            indent: AttributedText = AT(),
            ) -> None:

        if self._anchor_id == root_id:
            lines.lower_offset = -1

        # Do we have to draw a cursor?
        cursor = self._cursor_id == root_id

        # Render main message (root)
        rendered_lines = self._render_message(root_id, indent)
        lines.extend_below(rendered_lines)

        # Determine new indent
        extra_indent = self._render_indent(cursor=cursor)
        new_indent = indent + extra_indent

        # Render children
        for child_id in self._supply.child_ids(root_id):
            self._render_subtree(lines, child_id, new_indent)

        # Render cursor if necessary
        if cursor:
            # The cursor also acts as anchor if anchor is not specified
            if self._anchor_id is None:
                lines.lower_offset = -1

            cursor_indent = indent + self._render_indent(cursor_line=True)
            lines.extend_below(self._render_cursor(cursor_indent))

    def _render_tree(self, root_id: Id) -> AttributedLines:
        lines = AttributedLines()
        self._render_subtree(lines, root_id)
        return lines

    def _render_tree_containing(self, message_id: Id) -> AttributedLines:
        root_id = self._supply.root_id(message_id)
        return self._render_tree(root_id)

    def _expand_upwards_until(self,
            lines: AttributedLines,
            ancestor_id: Id,
            target_upper_offset: int,
            ) -> Tuple[Id, bool]:

        last_rendered_id = ancestor_id

        while True:
            next_id = self._supply.previous_id(last_rendered_id)

            if next_id is None:
                # We've hit the top of the supply
                return last_rendered_id, True

            if lines.upper_offset <= target_upper_offset:
                # We haven't hit the top, but the target has been satisfied
                return last_rendered_id, False

            lines.extend_above(self._render_tree(next_id))
            last_rendered_id = next_id

    def _expand_downwards_until(self,
            lines: AttributedLines,
            ancestor_id: Id,
            target_lower_offset: int,
            ) -> None:

        last_rendered_id = ancestor_id

        while True:
            next_id = self._supply.next_id(last_rendered_id)

            if next_id is None:
                # We've hit the bottom of the supply, but we might still have a
                # cursor to render
                break

            if lines.lower_offset >= target_lower_offset:
                return

            lines.extend_below(self._render_tree(next_id))
            last_rendered_id = next_id

        if self._cursor_id is None:
            lines.extend_below(self._render_cursor())

    # Rendering the lines

    def _render_lines_from_cursor(self) -> Tuple[AttributedLines, int, bool]:
        """
        Uses the following strategy:
        1. Render the cursor
        2. Render the lowest tree, if there is one
        3. Extend upwards until the top of the screen, if necessary
        """

        delta = 0

        # Step 1
        lines = self._render_cursor()
        lines.lower_offset = self._absolute_anchor_offset

        if lines.lower_offset < self._height - 1:
            delta = self._height - 1 - lines.lower_offset
            lines.lower_offset = self._height - 1

        # Step 2
        lowest_root_id = self._supply.lowest_root_id()
        if lowest_root_id is None:
            hit_top = True
        else:
            lines.extend_above(self._render_tree(lowest_root_id))

            # Step 3
            _, hit_top = self._expand_upwards_until(lines, lowest_root_id, 0)

        return lines, delta, hit_top

    def _render_lines_from_anchor(self,
            anchor_id: Id,
            ) -> Tuple[AttributedLines, int, bool]:
        """
        Uses the following strategy:
        1. Render the anchor's tree
        2. Extend upwards until the top of the screen
        3. Adjust the offset to match rule 2
        4. Extend downwards until the bottom of the screen
        5. Adjust the offset to match rule 1
        6. Extend upwards again until the top of the screen
        """

        delta = 0

        # Step 1
        ancestor_id = self._supply.root_id(anchor_id)
        lines = self._render_tree(ancestor_id)
        lines.upper_offset += self._absolute_anchor_offset

        # Step 2
        upper_id, hit_top = self._expand_upwards_until(lines, ancestor_id, 0)

        # Step 3
        if lines.upper_offset > 0:
            delta -= lines.upper_offset
            lines.upper_offset = 0 # = upper_offset - delta

        # Step 4
        self._expand_downwards_until(lines, ancestor_id, self._height - 1)

        # Step 5
        if lines.lower_offset < self._height - 1:
            delta += (self._height - 1) - lines.lower_offset
            lines.lower_offset = self._height - 1

        # Step 6
        if not hit_top and lines.upper_offset > 0:
            _, hit_top = self._expand_upwards_until(lines, upper_id, 0)

        return lines, delta, hit_top

    def _render_lines(self) -> Tuple[AttributedLines, int, bool]:
        if self._cursor_id is None and self._anchor_id is None:
            return self._render_lines_from_cursor()

        working_id: Id
        if self._anchor_id is None:
            working_id = self._cursor_id # type: ignore
        else:
            working_id = self._anchor_id

        return self._render_lines_from_anchor(working_id)

    def _render(self) -> int:
        lines, delta, hit_top = self._render_lines()

        self._lines = lines
        self._hit_top = hit_top

        return delta

    # Finally, another public function! :P

    def render(self, width: int, height: int) -> None:
        if width != self._width:
            self.invalidate_all()

        self._width = width
        self._height = height

        self._render()

    # Scrolling

    def _closest_to_middle(self) -> Tuple[Optional[Id], int]:
        """
        Finds the element/cursor closest to the middle of the screen, and its
        on-screen offset.

        Returns None instead of an Id if the cursor is the closest.
        """

        middle_index = self.get_absolute_offset(0.5, self._height)
        lines = list(self.lines)

        # This should never happen; there should always be at least a cursor.
        # I'm just being defensive here.
        if len(lines) < 1:
            return 0, middle_index

        if middle_index < self.lines.upper_offset:
            attrs, _ = lines[0]
            index = self.lines.upper_offset
        elif middle_index > self.lines.lower_offset:
            attrs, _ = lines[-1]
            index = self.lines.lower_offset
        else:
            attrs, _ = lines[middle_index - self.lines.upper_offset]
            index = middle_index

        mid = attrs.get("mid")
        # We know that all lines, including the cursor, have an offset.
        index -= attrs.get("offset") or 0

        return mid, index

    def _find_cursor_on_screen(self) -> Optional[int]:
        for index, line in enumerate(self.lines):
            attrs, _ = line

            if attrs.get("cursor"):
                return index

        return None

    def _apply_scrolloff(self) -> None:
        offset = self._absolute_anchor_offset
        offset = max(self._scrolloff, offset)
        offset = min(self._height - 1 - self._scrolloff, offset)
        self._absolute_anchor_offset = offset

    def _focus_on_visible_cursor(self) -> bool:
        index = self._find_cursor_on_screen()
        if index is not None:
            self._anchor_id = None
            self._absolute_anchor_offset = index
            return True

        return False

    def scroll(self, scroll_delta: int) -> None:
        self._absolute_anchor_offset += scroll_delta

        delta = self._render()
        if delta != 0:
            self._absolute_anchor_offset += delta + scroll_delta
            self._render()

        if not self._focus_on_visible_cursor():
            closest, offset = self._closest_to_middle()

            self._anchor_id = closest
            self._absolute_anchor_offset = offset

    # Moving the cursor

    def _element_id_above_cursor(self,
            cursor_id: Optional[Id],
            ) -> Optional[Id]:

        if cursor_id is None:
            cursor_id = self._supply.lowest_root_id()
            if cursor_id is None:
                return None # empty supply

        elem_id: Id = cursor_id
        while True:
            child_ids = self._supply.child_ids(elem_id)

            if child_ids:
                elem_id = child_ids[-1]
            else:
                return elem_id

    def _element_id_below_cursor(self,
            cursor_id: Optional[Id],
            ) -> Optional[Id]:

        above_id = self._element_id_above_cursor(cursor_id)
        if above_id is None:
            return None
        else:
            return self._supply.below_id(above_id)

    def _focus_on_offscreen_cursor(self) -> None:
        self._anchor_id = None

        # There is always at least one element above the cursor if the supply
        # isn't empty
        closest_id = self._element_id_above_cursor(self._cursor_id)
        if not closest_id:
            # The supply is empty
            self._anchor_offset = 0.5

        # This can't be the cursor id since the cursor is offscreen
        middle_id, _ = self._closest_to_middle()

        cursor_ancestor_path = self._supply.ancestor_path(closest_id)
        middle_ancestor_path = self._supply.ancestor_path(middle_id)

        if cursor_ancestor_path < middle_ancestor_path:
            # Cursor is above the screen somewhere
            self._anchor_offset = 0
        else:
            # Cursor is below the screen somewhere
            self._anchor_offset = 1

    def _focus_on_cursor(self) -> None:
        if not self._focus_on_visible_cursor():
            self._focus_on_offscreen_cursor()

        self._apply_scrolloff()

    def _cursor_visible(self) -> bool:
        return True in self.lines.all_values("cursor")

    def _height_of(self, between_ids: List[Id]) -> int:
        height = 0

        for mid in between_ids:
            message = self._cache.get(mid)
            if message is None:
                self._render_tree_containing(mid)
                message = self._cache.get(mid)

            if message is None:
                raise ShouldNeverHappen(1)

            height += len(message.lines)

        return height

    def move_cursor_up(self) -> None:
        new_cursor_id = self._supply.position_above_id(self._cursor_id)

        if new_cursor_id is None:
            # Already at the top
            self._focus_on_cursor()
            return

        above_old = self._element_id_above_cursor(self._cursor_id)
        below_new = self._element_id_below_cursor(new_cursor_id)

        if above_old is None:
            raise ShouldNeverHappen(2)

        # Moving horizontally at the bottom of the supply
        if below_new is None:
            height = 0
        else:
            between_ids = self._supply.between_ids(below_new, above_old)
            height = self._height_of(between_ids)

        self._cursor_id = new_cursor_id
        self._absolute_anchor_offset -= height
        self._render()
        self._focus_on_cursor()

    def move_cursor_down(self) -> None:
        if self._cursor_id is None:
            # Already at the bottom
            self._focus_on_cursor()
            return

        new_cursor_id = self._supply.position_below_id(self._cursor_id)

        below_old = self._element_id_below_cursor(self._cursor_id)
        above_new = self._element_id_above_cursor(new_cursor_id)

        if above_new is None:
            raise ShouldNeverHappen(3)

        # Moving horizontally at the bottom of the supply
        if below_old is None:
            height = 0
        else:
            between_ids = self._supply.between_ids(below_old, above_new)
            height = self._height_of(between_ids)

        self._cursor_id = new_cursor_id
        self._absolute_anchor_offset += height
        self._render()
        self._focus_on_cursor()

class BasicCursorRenderer(CursorRenderer):

    META_FORMAT = "%H:%M "
    META_WIDTH = 6

    @property
    def meta_width(self) -> int:
        return self.META_WIDTH

    def render_element(self, message: Message, width: int) -> RenderedMessage:
        meta = AT(message.timestamp.strftime(self.META_FORMAT))

        nick = AT(f"[{message.nick}] ")
        nick_spaces = AT(" " * len(nick))

        lines = []
        for i, line in enumerate(message.content.split("\n")):
            text = (nick if i == 0 else nick_spaces) + AT(line)
            lines.append(text)

        return RenderedMessage(message.id, lines, meta)

    def render_cursor(self, width: int) -> AttributedText:
        return AT("<cursor>")
