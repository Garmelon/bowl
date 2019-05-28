import urwid
import urwid.curses_display

import cheuph
from cheuph import AT, AttributedLines, AttributedLinesWidget


class TestWidget(urwid.WidgetWrap):
    def __init__(self):
        lines = [
                ({}, AT("a")),
                ({}, AT("Hello world")),
                ({}, AT("super long line " * 20)),
        ]
        self.lines = AttributedLinesWidget(AttributedLines(lines))
        super().__init__(self.lines)

    def selectable(self):
        return True

    def keypress(self, size, key):
        if key == "left":
            self.lines.horizontal_offset -= 1
        elif key == "right":
            self.lines.horizontal_offset += 1
        elif key == "home":
            self.lines.horizontal_offset = 0
        elif key == "up":
            self.lines.upper_offset += 1
        elif key == "down":
            self.lines.upper_offset -= 1

def main():
    screen = urwid.curses_display.Screen()
    loop = urwid.MainLoop(TestWidget(), screen=screen)
    loop.run()

main()
