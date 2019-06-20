import asyncio
from typing import Any, Awaitable, Callable, List, Optional, Tuple, TypeVar

import urwid
import yaboli

from ..attributed_text_widget import ATWidget
from ..cursor_rendering import CursorTreeRenderer
from ..cursor_tree_widget import CursorTreeWidget
from ..element import Message, RenderedMessage
from ..element_supply import InMemorySupply
from ..markup import AT, AttributedText, Attributes
from .edit_widgets import EditWidget
from .euph_renderer import EuphRenderer

__all__ = ["RoomWidget"]

# I don't know of a way to type the arguments correctly with mypy. You can't
# just substitute a Callable's parameter list with a type variable (sadly), and
# other workarounds didn't seem to solve this exact problem.
def synchronous(f: Any) -> Any:
    def wrapper(*args: Any, **kwargs: Any) -> None:
        asyncio.create_task(f(*args, **kwargs))
    return wrapper

class RoomLayout(urwid.WidgetWrap):
    def __init__(self,
            room_name: Any,
            nick_list: Any,
            tree: Any,
            edit: Any,
            nick_list_width: int = 24,
            border_attrs: Attributes = {},
            room_name_separator: str = "═",
            room_name_split: str = "╤",
            nick_list_separator: str = "│",
            nick_list_split: str = "┤",
            edit_separator: str = "─",
        ) -> None:

        self._width = 0
        self._height = 0
        self._redraw = True

        self._room_name = room_name
        self._nick_list = nick_list
        self._tree = tree
        self._edit = edit
        self._nick_list_width = nick_list_width
        self._border_attrs = border_attrs
        self._room_name_separator = room_name_separator
        self._room_name_split = room_name_split
        self._nick_list_separator = nick_list_separator
        self._nick_list_split = nick_list_split
        self._edit_separator = edit_separator

        # Placeholders (TODO: Use urwid.Text)
        self._room_name_divider = ATWidget(AT())
        self._nick_list_divider = ATWidget(AT())
        self._edit_divider = ATWidget(AT())

        self._edit_pile = urwid.Pile([
            self._tree,
            ("pack", self._edit_divider),
            ("pack", self._edit),
        ])
        self._edit_pile.focus_position = 2

        self._left_wrap = urwid.WidgetWrap(self._tree)

        self._columns = urwid.Columns([
            self._left_wrap,
            (1, urwid.Filler(self._nick_list_divider)),
            (self._nick_list_width, self._nick_list),
        ])
        self._columns.focus_position = 0

        self._outer_pile = urwid.Pile([
            ("pack", self._room_name),
            ("pack", self._room_name_divider),
            self._columns,
        ])
        self._outer_pile.focus_position = 2

        super().__init__(self._outer_pile)

    def render(self, size: Tuple[int, int], focus: bool) -> Any:
        self._width, self._height = size

        tree_width = self._width - self._nick_list_width - 1

        self._room_name_divider.set_attributed_text(
                self._render_room_name_divider(tree_width))
        self._nick_list_divider.set_attributed_text(
                self._render_nick_list_divider(tree_width))
        self._edit_divider.set_attributed_text(
                self._render_edit_divider(tree_width))

        return super().render(size, focus)

    def _render_room_name_divider(self, tree_width: int) -> AttributedText:
        string = (
                self._room_name_separator * tree_width +
                self._room_name_split +
                self._room_name_separator * self._nick_list_width
        )
        return AT(string, attributes=self._border_attrs)

    def _render_nick_list_divider(self, tree_width: int) -> AttributedText:
        height = self._height - self._room_name.rows((self._width,)) - 1

        if self._left_wrap._w is self._tree:
            lines = [self._nick_list_separator] * height
        else:
            edit_height = self._edit.rows((tree_width,))
            tree_height = height - edit_height - 1
            lines = (
                    [self._nick_list_separator] * tree_height +
                    [self._nick_list_split] +
                    [self._nick_list_separator] * edit_height
            )

        string = "\n".join(lines)
        return AT(string, attributes=self._border_attrs)

    def _render_edit_divider(self, tree_width: int) -> AttributedText:
        string = self._edit_separator * tree_width
        return AT(string, attributes=self._border_attrs)

    def set_edit_visible(self, visible: bool):
        if visible:
            self._left_wrap._w = self._edit_pile
        else:
            self._left_wrap._w = self._tree

    def focus_on_edit(self):
        self._edit_pile.focus_position = 2
        self._columns.focus_position = 0

    def focus_on_tree(self):
        self._edit_pile.focus_position = 0
        self._columns.focus_position = 0

    def focus_on_user_list(self):
        self._columns.focus_position = 2

class RoomWidget(urwid.WidgetWrap):
    """
    The RoomWidget connects to and displays a single yaboli room.

    Its life cycle looks like this:
    1. Create widget
    2. Call connect() (while the event loop is running)
    3. Keep widget around and occasionally display it
    4. Call disconnect() (while the event loop is runnning)
    5. When the room should be destroyed/forgotten about, it sends a "close"
       event
    """

    CONNECTING = "connecting"
    CONNECTION_FAILED = "connection_failed"
    VIEWING = "viewing"
    EDITING = "editing"

    def __init__(self,
            roomname: str,
            log_amount: int = 200,
            ) -> None:

        if log_amount < 1:
            raise ValueError() # TODO add better text
        self._log_amount = log_amount

        self._mode: str
        self._requesting_logs = False
        self._hit_top_of_supply = False

        self._room = yaboli.Room(roomname)
        self._room.register_event("snapshot", self.on_snapshot)
        self._room.register_event("send", self.on_send)

        self._supply = InMemorySupply[Message]()
        self._renderer = self._create_euph_renderer()
        self._tree = CursorTreeRenderer[Message](self._supply, self._renderer)

        # All of the widgets

        self._connecting = self._create_connecting_widget()
        self._connection_failed = self._create_connection_failed_widget()

        self._edit_nick = self._create_edit_nick_widget()
        #self._edit_password = self._create_password_edit_widget()
        #self._authenticating = self._create_authenticating_widget()

        self._room_name = self._create_room_name_widget()
        self._nick_list = self._create_nick_list_widget()
        self._tree_widget = self._create_tree_widget()
        self._edit = self._create_edit_widget()
        self._layout = self._create_room_layout_widget(self._room_name,
                self._nick_list, self._tree_widget, self._edit)

        self._box = urwid.LineBox(self._edit_nick)
        self._overlay = urwid.Overlay(
                self._box,
                self._layout,
                align=urwid.CENTER,
                width=(urwid.RELATIVE, 24),
                valign=urwid.MIDDLE,
                height=urwid.PACK,
        )

        super().__init__(self._connecting)
        self.switch_connecting()

    # Creating the various parts of the layout.
    #
    # This is put into separate methods because the individual elements have a
    # lot of parameters which are (to be) read from some sort of config system.
    # Putting all of these into __init__() would be a mess.
    #
    # These functions use (or rather: will use) self._conf.

    def _create_euph_renderer(self) -> EuphRenderer:
        return EuphRenderer("")

    def _create_connecting_widget(self) -> Any:
        text = (
                AT("Connecting to ") +
                AT("&" + self._room.name) +
                AT("...")
        )
        # Centered vertically and horizontally
        return urwid.Filler(ATWidget(text, align=urwid.CENTER))

    def _create_connection_failed_widget(self) -> Any:
        text = (
                AT("Could not connect to ") +
                AT("&" + self._room.name) +
                AT("...")
        )
        # Centered vertically and horizontally
        return urwid.Filler(ATWidget(text, align=urwid.CENTER))

    def _create_room_name_widget(self) -> Any:
        return urwid.Text("&" + self._room.name, align=urwid.CENTER)

    def _create_tree_widget(self) -> Any:
        return CursorTreeWidget(self._tree)

    def _create_edit_widget(self) -> Any:
        return urwid.Edit(multiline=True)

    def _create_nick_list_widget(self) -> Any:
        return urwid.SolidFill("n")

    def _create_room_layout_widget(self,
            room_name: Any,
            nick_list: Any,
            tree: Any,
            edit: Any,
            ) -> Any:
        return RoomLayout(room_name, nick_list, tree, edit)

    def _create_edit_nick_widget(self) -> Any:
        return EditWidget("Choose a nick: ", "@")

    ## Room life cycle

    @synchronous
    async def connect(self) -> None:
        success = await self._room.connect()
        if success:
            self.switch_view()
        else:
            self.switch_connection_failed()
            urwid.emit_signal(self, "close")

    @synchronous
    async def disconnect(self) -> None:
        await self._room.disconnect()
        # TODO attach this to the room's disconnect event instead
        urwid.emit_signal(self, "close")

    ## UI mode and mode switching

    CONNECTING = "connecting"
    CONNECTION_FAILED = "connection_failed"
    SETTING_PASSWORD = "setting_password"
    AUTHENTICATING = "authenticating"
    SETTING_NICK = "setting_nick"
    VIEWING = "viewing"
    EDITING = "editing"

    def switch_connecting(self) -> None:
        self._w = self._connecting
        self._mode = self.CONNECTING

    def switch_connection_failed(self) -> None:
        self._w = self._connection_failed
        self._mode = self.CONNECTION_FAILED

    def switch_setting_password(self) -> None:
        self._w = self._overlay
        self._overlay.set_top(self._edit_password)
        self._mode = self.SETTING_PASSWORD

    def switch_authenticating(self) -> None:
        self._w = self._overlay
        self._overlay.set_top(self._authenticating)
        self._mode = self.AUTHENTICATING

    def switch_setting_nick(self) -> None:
        self._w = self._overlay
        self._box.original_widget = self._edit_nick
        self._edit_nick.text = self._room.session.nick
        self.update_edit_nick()
        self._mode = self.SETTING_NICK

    def switch_view(self) -> None:
        self._w = self._layout
        self._layout.set_edit_visible(False)
        self._layout.focus_on_tree()
        self._mode = self.VIEWING

    def switch_edit(self) -> None:
        self._w = self._layout
        self._layout.set_edit_visible(True)
        self._layout.focus_on_edit()
        self._mode = self.EDITING

    # Updating various parts of the UI

    def update_tree(self) -> None:
        self._tree_widget._invalidate()

    def update_nick_list(self) -> None:
        # Ensure that self._room.session and self._room.users exist
        if self._mode not in {self.SETTING_NICK, self.VIEWING, self.EDITING}:
            return

        #self._nick_list.update(self._room.session, self._room.users)

    def update_edit_nick(self):
        width = self._edit_nick.width
        self._overlay.set_overlay_parameters(
                align=urwid.CENTER,
                width=width + 2, # for the LineBox
                valign=urwid.MIDDLE,
                height=urwid.PACK,
        )
        self._overlay._invalidate()

    # Reacting to changes

    def own_nick_change(self):
        self._renderer.nick = self._room.session.nick
        self._tree.invalidate_all()
        self.update_tree()
        self.update_nick_list()

    def receive_message(self, msg: yaboli.Message):
        self._supply.add(Message(
            msg.message_id,
            msg.parent_id,
            msg.time,
            msg.sender.nick,
            msg.content,
        ))
        self._tree.invalidate(msg.message_id)
        self.update_tree()

    ## Reacting to urwid stuff

    def render(self, size: Tuple[int, int], focus: bool) -> None:
        canvas = super().render(size, focus)

        if self._tree.hit_top and not self._requesting_logs:
            self._requesting_logs = True
            self.request_logs()

        return canvas

    def keypress(self, size: Tuple[int, int], key: str) -> Optional[str]:
        if self._mode == self.VIEWING:
            if key in {"enter", "meta enter"} and not self._room.session.nick:
                self.switch_setting_nick()
            elif key == "enter":
                self._edit.edit_text = ""
                self.switch_edit()
            elif key == "meta enter":
                self.switch_edit()
            elif key == "n":
                self.switch_setting_nick()
            elif key == "r":
                self._tree.invalidate_all()
                self._tree_widget._invalidate()
            elif key == "q":
                self.disconnect()
            else:
                return super().keypress(size, key)

        elif self._mode == self.EDITING:
            if key == "enter":
                if self._edit.edit_text:
                    self.send(self._edit.edit_text, self._tree.cursor_id)
                self.switch_view()
            elif key == "esc":
                self.switch_view()
            elif key == "meta enter":
                self._edit.insert_text("\n")
            else:
                return super().keypress(size, key)

        elif self._mode == self.SETTING_NICK:
            if key == "enter":
                if self._edit_nick.text:
                    self.nick(self._edit_nick.text)
                self.switch_view()
            elif key == "esc":
                self.switch_view()
            else:
                key = super().keypress(size, key)
                self.update_edit_nick()
                return key

        else:
            return super().keypress(size, key)

        return None

    ## Euph stuff

    # Reacting to euph events

    async def on_snapshot(self, messages: List[yaboli.Message]):
        for message in messages:
            self.receive_message(message)
        self.update_tree()

    async def on_send(self, message: yaboli.Message):
        self.receive_message(message)
        self.update_tree()

    # Euph actions

    @synchronous
    async def request_logs(self):
        oldest_id = self._supply.oldest_id()
        if oldest_id is not None:
            messages = await self._room.log(self._log_amount, oldest_id)
            for message in messages:
                self.receive_message(message)
            self.update_tree()

        self._requesting_logs = False

    @synchronous
    async def nick(self, nick: str):
        new_nick = await self._room.nick(nick)
        self.own_nick_change()

    @synchronous
    async def send(self, content: str, parent_id: Optional[str]):
        message = await self._room.send(content, parent_id=parent_id)
        self.receive_message(message)
        self.update_tree()

urwid.register_signal(RoomWidget, ["close"])
