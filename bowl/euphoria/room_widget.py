import asyncio
import pathlib
from enum import Enum
from typing import Any, Awaitable, Callable, List, Optional, Tuple, TypeVar

import urwid
import yaboli

from ..attributed_text_widget import ATWidget
from ..cursor_rendering import CursorRenderer, CursorTreeRenderer
from ..cursor_tree_widget import CursorTreeWidget
from ..element import Message, RenderedMessage
from ..element_supply import ElementSupply, InMemorySupply
from ..markup import AT, AttributedText, Attributes
from .edit_widgets import EditWidget
from .euph_config import EuphConfig
from .euph_renderer import EuphRenderer
from .nick_list_widget import NickListWidget

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

    def set_edit_visible(self, visible: bool) -> None:
        if visible:
            self._left_wrap._w = self._edit_pile
        else:
            self._left_wrap._w = self._tree

    def focus_on_edit(self) -> None:
        self._edit_pile.focus_position = 2
        self._columns.focus_position = 0

    def focus_on_tree(self) -> None:
        self._edit_pile.focus_position = 0
        self._columns.focus_position = 0

    def focus_on_nick_list(self) -> None:
        self._columns.focus_position = 2

class UiMode(Enum):

    CONNECTING = "connecting"
    CONNECTION_FAILED = "connection failed"
    SETTING_PASSWORD = "setting password"
    AUTHENTICATING = "authenticating"
    SETTING_NICK = "setting nick"
    VIEWING = "viewing"
    EDITING = "editing"

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

    def __init__(self,
            roomname: str,
            config: EuphConfig,
            log_amount: int = 200,
            ) -> None:

        self.c = config

        self._log_amount = log_amount
        if self._log_amount < 1:
            raise ValueError("log request amount must be at least 1")

        self._mode: UiMode
        self._requesting_logs = False
        self._hit_top_of_supply = False

        url_format = yaboli.Room.URL_FORMAT
        if self.c.human:
            url_format += "?h=1"

        cookie_file = self.c.cookie_file
        if cookie_file is not None:
            cookie_file = str(pathlib.Path(cookie_file).expanduser())

        self._room = yaboli.Room(
                roomname,
                url_format=url_format,
                cookie_file=cookie_file,
        )

        self._room.register_event("connected", self.on_connected)
        self._room.register_event("snapshot", self.on_snapshot)
        self._room.register_event("send", self.on_send)
        self._room.register_event("join", self.on_join)
        self._room.register_event("part", self.on_part)
        self._room.register_event("nick", self.on_nick)
        self._room.register_event("edit", self.on_edit)
        self._room.register_event("disconnect", self.on_disconnect)

        self._supply = InMemorySupply[Message]()
        self._renderer = self._create_euph_renderer()
        self._tree = self._create_cursor_tree_renderer(self._supply,
                self._renderer)

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
        return EuphRenderer(
                "",
                show_year=self.c.show_year,
                show_seconds=self.c.show_seconds,
                meta_attrs={"style": self.c.meta_style},
                surround_left=self.c.surround_left,
                surround_right=self.c.surround_right,
                surround_attrs={"style": self.c.surround_style},
                cursor_surround_left=self.c.cursor_surround_left,
                cursor_surround_right=self.c.cursor_surround_right,
                cursor_surround_attrs={"style": self.c.cursor_surround_style},
                cursor_own_nick_attrs={"style":self.c.cursor_own_nick_style},
                cursor_fill=self.c.cursor_fill_char,
                cursor_fill_attrs={"style": self.c.cursor_fill_style},
                nick_attrs={"style": self.c.nick_style},
                own_nick_attrs={"style": self.c.own_nick_style},
        )

    def _create_cursor_tree_renderer(self,
            supply: ElementSupply,
            renderer: CursorRenderer,
            ) -> CursorTreeRenderer:

        return CursorTreeRenderer(supply, renderer,
                indent_width=self.c.indent_width,
                indent=self.c.indent_char,
                indent_fill=self.c.indent_fill,
                indent_attrs={"style": self.c.indent_style},
                cursor_indent=self.c.indent_cursor_char,
                cursor_corner=self.c.indent_cursor_corner,
                cursor_fill=self.c.indent_cursor_fill,
                cursor_indent_attrs={"style": self.c.indent_cursor_style},
                scrolloff=self.c.scrolloff,
        )

    def _create_connecting_widget(self) -> Any:
        text = (
                AT("Connecting to ") +
                AT("&" + self._room.name, style=self.c.room_style) +
                AT("...")
        )
        # Centered vertically and horizontally
        return urwid.Filler(ATWidget(text, align=urwid.CENTER))

    def _create_connection_failed_widget(self) -> Any:
        text = (
                AT("Could not connect to ") +
                AT("&" + self._room.name, style=self.c.room_style) +
                AT("...")
        )
        # Centered vertically and horizontally
        return urwid.Filler(ATWidget(text, align=urwid.CENTER))

    def _create_room_name_widget(self) -> Any:
        return urwid.Text(
                (self.c.room_style, "&" + self._room.name),
                align=urwid.CENTER,
        )

    def _create_tree_widget(self) -> Any:
        return CursorTreeWidget(self._tree,
                vertical_scroll_step=self.c.vertical_scroll,
                horizontal_scroll_step=self.c.vertical_scroll,
                half_page_scroll=self.c.half_page_scroll,
        )

    def _create_edit_widget(self) -> Any:
        return urwid.Edit(multiline=True)

    def _create_nick_list_widget(self) -> Any:
        return NickListWidget(
                heading_attrs={"style": self.c.nick_list_heading_style},
                counter_attrs={"style": self.c.nick_list_counter_style},
                nick_attrs={"style": self.c.nick_style},
                own_nick_attrs={"style": self.c.own_nick_style},
        )

    def _create_room_layout_widget(self,
            room_name: Any,
            nick_list: Any,
            tree: Any,
            edit: Any,
            ) -> Any:
        return RoomLayout(room_name, nick_list, tree, edit,
                border_attrs={"style": self.c.borders_style},
                room_name_separator=self.c.room_name_separator,
                room_name_split=self.c.room_name_split,
                nick_list_separator=self.c.nick_list_separator,
                nick_list_split=self.c.nick_list_split,
                edit_separator=self.c.edit_separator,
        )

    def _create_edit_nick_widget(self) -> Any:
        return EditWidget("Choose a nick: ", "@", style=self.c.own_nick_style)

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

    def switch_connecting(self) -> None:
        self._w = self._connecting
        self._mode = UiMode.CONNECTING

    def switch_connection_failed(self) -> None:
        self._w = self._connection_failed
        self._mode = UiMode.CONNECTION_FAILED

    def switch_setting_password(self) -> None:
        self._w = self._overlay
        self._overlay.set_top(self._edit_password)
        self._mode = UiMode.SETTING_PASSWORD

    def switch_authenticating(self) -> None:
        self._w = self._overlay
        self._overlay.set_top(self._authenticating)
        self._mode = UiMode.AUTHENTICATING

    def switch_setting_nick(self) -> None:
        self._w = self._overlay
        self._box.original_widget = self._edit_nick
        self._edit_nick.text = self._room.session.nick
        self.update_edit_nick()
        self._mode = UiMode.SETTING_NICK

    def switch_view(self) -> None:
        self._w = self._layout
        self._layout.set_edit_visible(False)
        self._layout.focus_on_tree()
        self._mode = UiMode.VIEWING

    def switch_edit(self) -> None:
        self._w = self._layout
        self._layout.set_edit_visible(True)
        self._layout.focus_on_edit()
        self._mode = UiMode.EDITING

    # Updating various parts of the UI

    def update_tree(self) -> None:
        self._tree_widget._invalidate()

    def update_nick_list(self) -> None:
        # Ensure that self._room.session and self._room.users exist
        allowed = {UiMode.SETTING_NICK, UiMode.VIEWING, UiMode.EDITING}
        if self._mode not in allowed:
            return

        # Automatically rerenders
        self._nick_list.session = self._room.session
        self._nick_list.users = self._room.users

    def update_edit_nick(self) -> None:
        width = self._edit_nick.width
        self._overlay.set_overlay_parameters(
                align=urwid.CENTER,
                width=width + 2, # for the LineBox
                valign=urwid.MIDDLE,
                height=urwid.PACK,
        )
        self._overlay._invalidate()

    def change_own_nick(self) -> None:
        self._renderer.nick = self._room.session.nick
        self._tree.invalidate_all()
        self.update_tree()

        self._nick_list.session = self._room.session
        self.update_nick_list()

    def receive_message(self, msg: yaboli.Message) -> None:
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

        if not self._hit_top_of_supply:
            if self._tree.hit_top and not self._requesting_logs:
                self._requesting_logs = True
                self.request_logs()

        return canvas

    def keypress(self, size: Tuple[int, int], key: str) -> Optional[str]:
        if self._mode == UiMode.VIEWING:
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

        elif self._mode == UiMode.EDITING:
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

        elif self._mode == UiMode.SETTING_NICK:
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

    async def on_connected(self) -> None:
        pass

    async def on_snapshot(self, messages: List[yaboli.LiveMessage]) -> None:
        for message in messages:
            self.receive_message(message)

        self.change_own_nick()
        self.update_nick_list()

    async def on_send(self, message: yaboli.LiveMessage) -> None:
        self.receive_message(message)

    async def on_join(self, user: yaboli.LiveSession) -> None:
        self.update_nick_list()

    async def on_part(self, user: yaboli.LiveSession) -> None:
        self.update_nick_list()

    async def on_nick(self,
            user: yaboli.LiveSession,
            from_: str,
            to: str,
            ) -> None:

        self.update_nick_list()

    async def on_edit(self, message: yaboli.LiveMessage) -> None:
        self.receive_message(message)

    async def on_disconnect(self, reason: str) -> None:
        pass

    # Euph actions

    @synchronous
    async def request_logs(self) -> None:
        oldest_id = self._supply.oldest_id()
        if oldest_id is not None:
            messages = await self._room.log(self._log_amount, oldest_id)

            if len(messages) == 0:
                self._hit_top_of_supply = True

            for message in messages:
                self.receive_message(message)

        self._requesting_logs = False

    @synchronous
    async def nick(self, nick: str) -> None:
        try:
            await self._room.nick(nick)
            self.change_own_nick()
        except yaboli.EuphException:
            pass

    @synchronous
    async def send(self, content: str, parent_id: Optional[str]) -> None:
        message = await self._room.send(content, parent_id=parent_id)
        self.receive_message(message)

urwid.register_signal(RoomWidget, ["close"])
