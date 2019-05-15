from typing import Any, Optional

import urwid

from .palette import Style
from .room_widget import RoomWidget

__all__ = ["SingleRoomApplication"]

class ChooseRoomWidget(urwid.WidgetWrap):
    def __init__(self) -> None:
        self.error = None
        self.text = urwid.Text("Choose a room:", align=urwid.CENTER)
        self.edit = urwid.Edit("&", align=urwid.CENTER)
        self.pile = urwid.Pile([
            self.text,
            urwid.AttrMap(self.edit, Style.ROOM),
        ])
        self.filler = urwid.Filler(self.pile)
        super().__init__(self.filler)

    def render(self, size: Any, focus: Any) -> Any:
        if self.error:
            width, _ = size
            rows = self.error.rows((width,), focus)
            self.filler.bottom = rows

        return super().render(size, focus)

    def set_error(self, text: Any) -> None:
        self.error = urwid.Text(text, align=urwid.CENTER)
        self.pile = urwid.Pile([
            self.error,
            self.text,
            urwid.AttrMap(self.edit, Style.ROOM),
        ])
        self.filler = urwid.Filler(self.pile)
        self._w = self.filler

    def unset_error(self) -> None:
        self.error = None
        self.pile = urwid.Pile([
            self.text,
            urwid.AttrMap(self.edit, Style.ROOM),
        ])
        self.filler = urwid.Filler(self.pile)
        self._w = self.filler

    def could_not_connect(self, roomname: str) -> None:
        text = [
                "Could not connect to ",
                (Style.ROOM, "&" + roomname),
                ".\n",
        ]
        self.set_error(text)

    def invalid_room_name(self, reason: str) -> None:
        text = [f"Invalid room name: {reason}\n"]
        self.set_error(text)

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

    def __init__(self) -> None:
        self.choose_room = ChooseRoomWidget()
        super().__init__(self.choose_room)

    def selectable(self) -> bool:
        return True

    def switch_to_choose(self) -> None:
        self.choose_room.could_not_connect(self.choose_room.edit.edit_text)
        self._w = self.choose_room

    def keypress(self, size: Any, key: str) -> Optional[str]:
        if self._w == self.choose_room:
            if key == "esc":
                raise urwid.ExitMainLoop()

            self.choose_room.unset_error()

            if key == "enter":
                roomname = self.choose_room.edit.edit_text

                if roomname:
                    room = RoomWidget(roomname)
                    urwid.connect_signal(room, "close", self.switch_to_choose)
                    room.connect()
                    self._w = room
                else:
                    self.choose_room.invalid_room_name("too short")

            # Make sure we only enter valid room names
            elif key.lower() in self.ALPHABET:
                return super().keypress(size, key.lower())
            elif key in self.ALLOWED_EDITOR_KEYS:
                return super().keypress(size, key)

            return None

        else:
            return super().keypress(size, key)
