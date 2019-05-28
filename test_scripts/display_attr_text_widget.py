import urwid
import urwid.curses_display

import cheuph
from cheuph import AT, AttributedTextWidget


class TestWidget(urwid.WidgetWrap):
    def __init__(self):
        text = AT("Hello world!\nThis is some text.\nThird line.")
        self.text = AttributedTextWidget(text)
        self.filler = urwid.Filler(self.text)
        super().__init__(self.filler)

def main():
    screen = urwid.curses_display.Screen()
    loop = urwid.MainLoop(TestWidget(), screen=screen)
    loop.run()

main()
