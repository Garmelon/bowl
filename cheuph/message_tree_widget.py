from typing import Optional, Set

import urwid
import yaboli

from .attributed_lines_widget import AttributedLinesWidget
from .message import Id
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

    ROOM_IS_EMPTY = "<no messages>"

    def __init__(self,
            room: yaboli.Room,
            supply: MessageSupply,
            ) -> None:

        self.room = room
        self.supply = supply
        self.rendered = RenderedMessageCache()
        self.lines = AttributedLinesWidget()
        self.placeholder = urwid.Filler(urwid.Text(self.ROOM_IS_EMPTY,
            align=urwid.CENTER))

        # If the anchor is None, but the cursor isn't, the cursor is used as
        # the anchor.
        self.cursor: Optional[Id] = None
        self.anchor: Optional[Id] = None
        self.anchor_offset = 0

        self.folds: Set[Id] = set()

        super().__init__(self.placeholder)

    def invalidate_message(self, message_id: Id) -> None:
        pass

    def invalidate_all_messages(self) -> None:
        pass

    def redraw(self) -> None:
        pass
