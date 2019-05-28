import urwid
import urwid.curses_display

import cheuph
from cheuph import AT, AttributedLines, AttributedLinesWidget


class TestWidget(urwid.WidgetWrap):
    def __init__(self):
        long_line = AT("super", style="red")
        long_line += AT(" long", style="cyan")
        long_line += AT(" line", style="magenta")
        lines = [
                ({}, AT("abc", style="green")),
                ({"style": "blue"}, AT("Hello world")),
                ({}, AT(" ").join([long_line] * 10)),
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

    def mouse_event(self, size, event, button, col, row, focus):
        if event == "mouse press":
            if button == 4:
                self.lines.upper_offset += 1
            if button == 5:
                self.lines.upper_offset -= 1

def main():
    screen = urwid.curses_display.Screen()
    palette = [
            ("red", "light red", ""),
            ("yellow", "yellow", ""),
            ("green", "light green", ""),
            ("blue", "light blue", ""),
            ("magenta", "light magenta", ""),
            ("cyan", "light cyan", ""),
    ]
    loop = urwid.MainLoop(
            TestWidget(),
            screen=screen,
            palette=palette,
        )
    loop.run()

main()
