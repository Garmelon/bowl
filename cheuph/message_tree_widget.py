from typing import Optional, Set

import urwid

import yaboli

from .attributed_lines import AttributedLines
from .attributed_lines_widget import AttributedLinesWidget
from .markup import AT, AttributedText
from .message import Id, RenderedMessage
from .message_supply import MessageSupply
from .rendered_message_cache import RenderedMessageCache

__all__ = ["MessageTreeWidget"]


class MessageTreeWidget(urwid.WidgetWrap):
    """
    This widget displays an ElementSupply, including user interface like a
    cursor or folding markers. It usually is part of a RoomWidget. It also
    keeps a RenderedMessageCache (and maybe even other caches).

    It receives key presses and mouse clicks from its parent widget. It
    receives redraw requests and cache invalidation notices from the
    RoomWidget.

    It doesn't directly receive new messages. Rather, the RoomWidget adds them
    to the ElementSupply and then submits a cache invalidation notice and a
    redraw request.

    It emits a "room top hit" event (unnamed as of yet). When the RoomWidget
    receives this event, it should retrieve more messages from the server.

    It emits a "edit" event (unnamed as of yet) when the user attempts to edit
    a message. When the RoomWidget receives this event, it should open a text
    editor to compose a new message, and send that message once the user
    finishes editing it.
    """

    ROOM_IS_EMPTY_MESSAGE = "<no messages>"

    def __init__(self,
            # TODO config
            room: yaboli.Room,
            supply: MessageSupply,
            ) -> None:

        # yaboli.Room, used only for the current nick
        self.room = room
        # A supply of Message-s
        self.supply = supply
        # A cache of RenderedMessage-s
        self.rendered = RenderedMessageCache()
        # The lines that were last rendered
        self.lines = AttributedLines()
        #
        # Widget tha displays self.lines
        self.lines_widget = AttributedLinesWidget()
        # A placeholder if there are no messages to display
        self.placeholder = urwid.Filler(urwid.Text(self.ROOM_IS_EMPTY_MESSAGE,
            align=urwid.CENTER))

        # The id of the message that the cursor is displayed under.
        self.cursor_id: Optional[Id] = None
        # If the anchor is None, but the cursor isn't, the cursor is used as
        # the anchor.
        self.anchor_id: Optional[Id] = None
        # The anchor's line's offset on the screen, measured in percent of the
        # total height. For more information, see the comment above
        # _get_absolute_offset() and _get_relative_offset().
        self.anchor_offset = 0.5

        # The last known width (use this to invalidate the cache when needed)
        self.width = 80
        # Columns per indentation level
        self.indent_width = 2
        # Columns at beginning of line that are reserved for date etc.
        self.meta_width = 6 # "HH:MM "
        # Columns at the end to mark overlapping lines
        self.overlap_width = 1

        # Which sub-threads are folded
        #self.folds: Set[Id] = set() # TODO

        super().__init__(self.placeholder)

    @property
    def usable_width(self) -> int:
        """
        The width that's available for everything, while staying inside the
        bounds of the overlap indicators.
        """

        return self.width - self.overlap_width

    @property
    def content_width(self) -> int:
        """
        The width that's left over for messages and their indentation
        information, after meta_width etc. are removed.
        """

        return self.usable_width - self.meta_width

    # Offsets

    """
    On offsets:

    An offset of 0.0 describes the middle of the first line on screen, whereas
    an offset of 1.0 describes the middle of the last line on screen.

    An example:

    line 0 - 0.0
    line 1 - 0.25
    line 2 - 0.5
    line 3 - 0.75
    line 4 - 1.0

    Let l be a line's index (starts with 0), o the offset and n the number of
    lines visible on the screen.

    OFFSET -> LINE NUMBER

    l = round(o * (n - 1))

    LINE NUMBER -> OFFSET

    o = l / (n - 1)

    Be careful if only one line is visible on the screen! Setting o to 0.5 is
    recommended in that case.
    """

    @staticmethod
    def _get_absolute_offset(offset: float, height: int) -> int:
        return round(offset * (height - 1))

    @staticmethod
    def _get_relative_offset(line: int, height: int) -> float:
        if height <= 1:
            return 0.5

        return line / (height - 1)

    @property
    def absolute_anchor_offset(self) -> int:
        return self._get_absolute_offset(self.anchor_offset, self.height)

    @absolute_anchor_offset.setter
    def absolute_anchor_offset(self, offset: int) -> None:
        self.anchor_offset = self._get_relative_offset(offset, self.height)

    # Message cache operations and maintenance

    def invalidate_message(self, message_id: Id) -> None:
        """
        Invalidate the RenderedMessage cached under message_id.
        """

        pass # TODO

    def invalidate_all_messages(self) -> None:
        """
        Invalidate all cached RenderedMessage-s.
        """

        pass # TODO

    # Rendering a single message

    def _render_message(self, message_id: Id, width: int) -> RenderedMessage:
        """
        Somehow obtain a RenderedMessage for the specified message_id.

        If the cache does not contain this message yet, or if it contains an
        invalid message (wrong width), the message is rendered and then added
        to the cache. Otherwise, the cached message is returned.
        """

        cached = self.cache.get(message_id)

        if cached.width != width:
            self.invalidate_message(message_id)
            cached = None

        if cached is not None:
            return cached

        message = self.supply.get(message_id)
        # TODO give current Room to message so it knows the current nick(s)
        # TODO give current meta format to message
        rendered = message.render(width)
        self.cache.set(message_id, rendered)
        return rendered

    def _render_message_lines(self,
            message_id: Id,
            indent: AttributedText = AT(),
            ) -> AttributedLines:
        """
        Render the message with the specified id into AttributedLines.

        The lines have the format:

        <meta><indent><nick and content>

        Each line has the following line-wide attributes:

        - mid - the id of the message
        - offset - the offset to the message's topmost line
        """

        width = self.content_width - len(indent)
        rendered = self._render_message(message_id, width)

        meta = rendered.meta
        meta_spaces = AT(" " * len(rendered.meta))

        lines = AttributedLines()

        mid = rendered.message_id
        offset = 0

        lines.append_below({"mid": mid, "offset": offset},
                meta + indent + rendered.lines[0])

        for line in rendered.lines[1:]:
            offset += 1
            lines.append_below({"mid": mid, "offset": offset},
                    meta_spaces + indent + line)

        return lines

    def _render_cursor(self, indent: AttributedText = AT()) -> AttributedLines:
        pass # TODO

    # Rendering the tree

    def _render_tree(self, root_id: Id) -> AttributedLines:
        """
        A wrapper around _render_subtree(), for ease of use.

        Doesn't adjust the offset; the AttributedLines returned does NOT take
        into account the attribute_offset.
        """

        lines = AttributedLines()
        self.render_subtree(lines, root_id)
        return lines

    def _render_subtree(self,
            lines: AttributedLines,
            root_id: Id,
            indent: AttributedText = AT(),
            ) -> None:
        """
        Render a (sub-)tree to the AttributedLines specified.

        This function also sets the vertical offset to be 0 on the anchor's
        first line, or the cursor's first (and only) line if the cursor is the
        anchor.

        - lines - the AttributedLines object to render to
        - root_id - the id of the message to start rendering at
        - indent - the indent string to prepend
        """

        if self.anchor_id == root_id:
            lines.lower_offset = -1

        # Render main message (root)
        rendered = self._render_message_lines(root_id, indent)
        lines.extend_below(rendered)

        # Determine new indent
        extra_indent = AT("┃ " if self.cursor_id == root_id else "│ ")
        new_indent = indent + extra_indent

        # Render children
        for child_id in self.supply.children_ids(root_id):
            self._render_subtree(lines, child_id, new_indent)

        # Render cursor if necessary
        if self.cursor_id == root_id:
            # The cursor also acts as anchor if anchor is not specified
            if self.anchor_id is None:
                lines.lower_offset = -1

            cursor_indent = indent + AT("┗━")
            lines.extend_below(self._render_cursor(indent))

    def _render_tree_containing(self, message_id: Id) -> AttributedLines:
        """
        Similar to _render_tree(), but finds the root of the specified message
        first.
        """

        root_id = self.supply.oldest_ancestor_id(message_id)
        # Puts the message with the specific id into the cache
        return self._render_tree(root_id)

    def _expand_upwards_until(self,
            lines: AttributedLines,
            ancestor_id: Id,
            target_upper_offset: int,
            ) -> Id:
        """
        Render trees and prepend them to the AttributedLines until its
        upper_offset matches or exceeds the target_upper_offset.

        Returns the last tree id that was rendered. If no tree could be
        rendered, returns the original anchor id.

        Starts at the first older sibling of the ancestor_id (the first sibling
        above the ancestor_id) and moves upwards sibling by sibling. Does not
        render the ancestor_id itself.
        """

        # This loop doesn't use a condition but rather break-s, because I think
        # it looks cleaner that way. I don't like mixing conditions and breaks
        # too much, if the conditions are of the same importance.
        last_rendered_id = ancestor_id

        while True:
            if lines.upper_offset <= target_upper_offset: break

            next_id = self.supply.previous_id(last_rendered_id)
            if next_id is None: break

            lines.extend_above(self._render_tree(next_id))
            last_rendered_id = next_id

        return last_rendered_id

    def _expand_downwards_until(self,
            lines: AttributedLines,
            ancestor_id: Id,
            target_lower_offset: int,
            ) -> Id:
        """
        Render trees and append them to the AttributedLines until its
        lower_offset matches or exceeds the target_lower_offset.

        Returns the last tree id that was rendered. If no tree could be
        rendered, returns the original anchor id.

        Starts at the first younger sibling of the ancestor_id (the first
        sibling below the ancestor_id) and moves downwards sibling by sibling.
        Does not render the ancestor_id itself.
        """

        # Almost the same as _expand_upwards_until(), but with small changes.
        # Maybe these could one day be combined into one function.
        #
        # This loop doesn't use a condition but rather break-s, because I think
        # it looks cleaner that way. I don't like mixing conditions and breaks
        # too much, if the conditions are of the same importance.

        last_rendered_id = ancestor_id

        while True:
            if lines.upper_offset >= target_lower_offset: break

            next_id = self.supply.next_id(last_rendered_id)
            if next_id is None: break

            lines.extend_below(self._draw_tree(next_id))
            last_rendered_id = next_id

        return last_rendered_id

    # Rendering the screen

    def _render_screen(self) -> AttributedLines:
        """
        Render an AttributedLines that fills the screen (as far as possible),
        taking into account the anchor offset.

        This does NOT fix scrolling (i. e. by min()- or max()-ing the upper and
        lower offsets). Instead, scrolling should be fixed when the anchor
        offset is changed or the resolution changes.
        """

        # TODO maybe extend with an additional offset for scrolling

        lines: AttributedLines

        if self.cursor_id is None:
            # If the cursor is None, that means that it should always be
            # displayed at the very bottom of the room. It also means that
            # _render_subtree() can't render the cursor, because it would be
            # the root of a message tree.

            if self.anchor_id is None:
                # Start with the cursor
                lines = self._render_cursor()
                lines.upper_offset = self.absolute_anchor_offset
                # Then expand upwards
                lowest_root_id = self.supply.lowest_root_id()
                if lowest_root_id is not None:
                    self._expand_upwards_until(lines, lowest_root_id, 0)
            else:
                # Start with the anchor as usual
                lines = self._render_tree_containing(self.anchor_id)
                lines.upper_offset += self.absolute_anchor_offset
                # And expand until the screen is full
                self._expand_upwards_until(lines, self.anchor_id, 0)
                until_id = self._expand_downwards_until(lines, self.anchor_id,
                        self.height - 1)
                # After that, draw the cursor below, if necessary
                lowest_root_id = self.supply.lowest_root_id()
                if until_id == lowest_root_id:
                    lines.extend_below(self._render_cursor())
        else:
            # In this case, the cursor is automatically rendered correctly by
            # _render_subtree(), so we actually don't have to do a lot.
            #
            # This case is the normal case, and the case I thought of first
            # when I designed this part.

            working_id: Id
            if self.anchor_id is None:
                working_id = self.cursor_id
            else:
                working_id = self.anchor_id

            ancestor_id = self.supply.oldest_ancestor_id(working_id)
            lines = self._render_tree(ancestor_id)
            lines.upper_offset += self.absolute_anchor_offset
            self._expand_upwards_until(lines, ancestor_id, 0)
            self._expand_downwards_until(lines, ancestor_id,
                    self.height - 1)

        return lines

    # Updating the internal widget

    def redraw(self) -> None:
        """
        Render new lines and draw them (to the internal widget and thus to the
        screen on the next screen update).
        """

        lines = self._render_screen()
        self.lines_widget.set_lines(lines)
        self._w = self.lines_widget
        self._invalidate() # Just to make sure this really gets rendered

    # Cursor movement

    # Scrolling
