import asyncio
from typing import Any, List, Optional

import urwid
import yaboli

from ..config import Config
from ..markup import AT
from ..widgets import ATWidget


class CenteredTextWidget(urwid.WidgetWrap):
    def __init__(self, lines: List[AT]):
        max_width = max(map(len, lines))
        text = AT("\n").join(lines)
        filler = urwid.Filler(ATWidget(text, align="center"))
        super().__init__(filler)

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

    def __init__(self, config: Config, roomname: str) -> None:
        self.c = config
        self._room = yaboli.Room(roomname)

        super().__init__(self._connecting_widget())
        self._room_view = self._connected_widget()

    def _connecting_widget(self) -> Any:
        lines = [AT("Connecting to ")
                + AT("&" + self.room.name, style=self.c.v.element.room)
                + AT("...")]
        return CenteredTextWidget(lines)

    def _connected_widget(self) -> Any:
        lines = [AT("Connected to ")
                + AT("&" + self.room.name, style=self.c.v.element.room)
                + AT(".")]
        return CenteredTextWidget(lines)

    def _connection_failed_widget(self) -> Any:
        lines = [AT("Could not connect to ")
                + AT("&" + self.room.name, style=self.c.v.element.room)
                + AT(".")]
        return CenteredTextWidget(lines)

    @property
    def room(self) -> yaboli.Room:
        return self._room

# Start up the connection and room

    async def _connect(self) -> None:
        success = await self._room.connect()
        if success:
            self._w = self._room_view
        else:
            self._w = self._connection_failed_widget()
            urwid.emit_signal(self, "close")

    def connect(self) -> None:
        asyncio.create_task(self._connect())

# Handle input

    #def selectable(self) -> bool:
    #    return True

    #def keypress(self, size: Any, key: str) -> Optional[str]:
    #    pass

urwid.register_signal(RoomWidget, ["close"])
