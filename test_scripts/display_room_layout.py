import urwid
import urwid.curses_display

import cheuph
from cheuph import AT, AttributedTextWidget
from cheuph.euphoria.room_widget import RoomLayout


def main():
    widget = RoomLayout(
            AttributedTextWidget(AT("&test"), align=urwid.CENTER),
            urwid.SolidFill("n"),
            urwid.SolidFill("t"),
            AttributedTextWidget(AT("edit\ning")),
            nick_list_width = 15,
            border_attrs = {"style": "dim"},
    )
    widget.set_edit_visible(True)
    palette = [
            ("dim", "dark gray,bold", ""),
    ]
    screen = urwid.curses_display.Screen()
    loop = urwid.MainLoop(
            widget,
            palette=palette,
            #screen=screen,
    )
    loop.run()

main()
