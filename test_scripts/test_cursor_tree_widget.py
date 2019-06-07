import datetime

import urwid
import urwid.curses_display

import cheuph
from cheuph import (AT, BasicCursorRenderer, CursorTreeRenderer,
                    CursorTreeWidget, InMemorySupply, Message)


def add(supply, level, text, amount=4):
    t = datetime.datetime(2019, 5, 7, 13, 25, 6)
    if level < 0: return
    for i in range(amount):
        new_text = f"{text}->{i}"
        supply.add(Message(new_text, text or None, t, str(i), new_text))
        add(supply, level - 1, new_text, amount=amount)

def main():
    s = InMemorySupply()
    r = BasicCursorRenderer()
    t = CursorTreeRenderer(s, r)

    add(s, 4, "")

    #screen = urwid.curses_display.Screen()
    event_loop = urwid.AsyncioEventLoop()
    loop = urwid.MainLoop(
            cheuph.CursorTreeWidget(t),
            #screen=screen,
            event_loop=event_loop,
    )
    loop.run()

main()
