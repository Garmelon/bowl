from typing import Any, Optional

import urwid

from .palette import Style
from .room_widget import RoomWidget

__all__ = ["SingleRoomApplication"]

class ChooseRoomWidget(urwid.WidgetWrap):
    def __init__(self) -> None:
        self.text = urwid.Text("Choose a room:", align="center")
        self.edit = urwid.Edit("&", align="center")
        self.pile = urwid.Pile([
            self.text,
            urwid.AttrMap(self.edit, Style.ROOM),
        ])
        self.filler = urwid.Filler(self.pile)
        super().__init__(self.filler)

    def set_error(self, text: Any) -> None:
        self.error = urwid.Text(text, align="center")
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

    def invalid_room_name(self) -> None:
        # TODO animate the invalid room name thingy?
        text = ["Invalid room name.\n"]
        self.set_error(text)

class SingleRoomApplication(urwid.WidgetWrap):
    ALPHABET = "abcdefghijklmnopqrstuvwxyz"
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
            # This leads to the editor jumping around the screen.
            #
            # TODO Find a way for the editor to stay still.
            self.choose_room.unset_error()

            if key == "enter":
                roomname = self.choose_room.edit.edit_text

                if roomname:
                    room = RoomWidget(roomname)
                    urwid.connect_signal(room, "close", self.switch_to_choose)
                    room.connect()
                    self._w = room

            # Make sure we only enter valid room names
            elif key.lower() in self.ALPHABET:
                return super().keypress(size, key.lower())
            elif key in self.ALLOWED_EDITOR_KEYS:
                return super().keypress(size, key)

            return None

        else:
            return super().keypress(size, key)
