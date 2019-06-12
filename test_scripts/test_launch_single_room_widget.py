import asyncio
import logging
from typing import List, Optional

import urwid

from cheuph.euphoria.single_room_application import SingleRoomApplication

logging.disable()

def main():
    loop = asyncio.get_event_loop()
    main_loop = urwid.MainLoop(
        SingleRoomApplication(),
        event_loop=urwid.AsyncioEventLoop(loop=loop),
    )

    main_loop.run()

if __name__ == "__main__":
    main()
