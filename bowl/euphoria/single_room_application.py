from typing import Any, Optional

import urwid

from ..attributed_text_widget import ATWidget
from ..markup import AT
from .edit_widgets import EditWidget
from .euph_config import EuphConfig
from .launch_application import launch
from .room_widget import RoomWidget

__all__ = ["SingleRoomApplication", "launch_single_room_application"]

class ChooseRoomWidget(urwid.WidgetWrap):

    def __init__(self,
            room_style: Optional[str] = None,
            error_style: Optional[str] = None,
            error_room_style: Optional[str] = None,
            ) -> None:

        self._room_style = room_style
        self._error_style = error_style
        self._error_room_style = error_room_style

        self.error = None
        self.edit = EditWidget("Choose a room:", caption="&", style=room_style)
        self.filler = urwid.Filler(self.edit)
        super().__init__(self.filler)

    def render(self, size: Any, focus: Any) -> Any:
        if self.error:
            width, _ = size
            rows = self.error.rows((width,), focus)
            self.filler.bottom = rows

        return super().render(size, focus)

    def set_error(self, text: Any) -> None:
        self.error = text
        self.pile = urwid.Pile([
            self.error,
            self.edit,
        ])
        self.filler = urwid.Filler(self.pile)
        self._w = self.filler

    def unset_error(self) -> None:
        self.error = None
        self.filler = urwid.Filler(self.edit)
        self._w = self.filler

    def could_not_connect(self, roomname: str) -> None:
        text = AT("Could not connect to ", style=self._error_style)
        text += AT("&" + roomname, style=self._error_room_style)
        text += AT(".\n", style=self._error_style)

        self.set_error(ATWidget(text, align=urwid.CENTER))

    def invalid_room_name(self, reason: str) -> None:
        text = AT(f"Invalid room name: {reason}\n",
                style=self._error_style)
        self.set_error(ATWidget(text, align=urwid.CENTER))

class SingleRoomApplication(urwid.WidgetWrap):

    # The characters in the ALPHABET make up the characters that are allowed in
    # room names.
    ALPHABET = "abcdefghijklmnopqrstuvwxyz0123456789"

    # These are other characters or character combinations necessary for the
    # editor to function well.
    ALLOWED_EDITOR_KEYS = {
            "backspace", "delete",
            "left", "right",
            "home", "end",
    }

    def __init__(self, config: EuphConfig) -> None:
        self.c = config

        self.choose_room = ChooseRoomWidget(
                room_style=self.c.room_style,
                error_style=self.c.error_style,
                error_room_style=self.c.error_room_style,
        )
        super().__init__(self.choose_room)

    def selectable(self) -> bool:
        return True

    def switch_to_choose(self) -> None:
        self.choose_room.could_not_connect(self.choose_room.edit.text)
        self._w = self.choose_room

    def keypress(self, size: Any, key: str) -> Optional[str]:
        if self._w is self.choose_room:
            if key == "esc":
                raise urwid.ExitMainLoop()

            self.choose_room.unset_error()

            if key == "enter":
                roomname = self.choose_room.edit.text

                if roomname:
                    room = RoomWidget(roomname, self.c)
                    urwid.connect_signal(room, "close", self.switch_to_choose)
                    self._w = room
                    room.connect()
                else:
                    self.choose_room.invalid_room_name("too short")

            elif not super().selectable():
                return key
            # Make sure we only enter valid room names
            elif key.lower() in self.ALPHABET:
                return super().keypress(size, key.lower())
            elif key in self.ALLOWED_EDITOR_KEYS:
                return super().keypress(size, key)

            return None

        elif super().selectable():
            return super().keypress(size, key)

        return key

def launch_single_room_application() -> None:
    launch(SingleRoomApplication)
