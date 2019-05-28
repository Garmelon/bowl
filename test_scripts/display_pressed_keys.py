import urwid
import urwid.curses_display

class TestWidget(urwid.WidgetWrap):
    KEY_LIMIT = 10

    def __init__(self):
        self.last_keys = []
        self.text = urwid.Text("No key pressed yet", align=urwid.CENTER)
        self.filler = urwid.Filler(self.text)
        super().__init__(self.filler)

    def selectable(self):
        return True

    def keypress(self, size, key):
        self.last_keys.append(repr(key))
        self.last_keys = self.last_keys[-self.KEY_LIMIT:]
        self.text.set_text("\n".join(self.last_keys))

    def mouse_event(self, size, event, button, col, row, focus):
        self.last_keys.append(f"{event!r} {button!r} ({row}, {col})")
        self.last_keys = self.last_keys[-self.KEY_LIMIT:]
        self.text.set_text("\n".join(self.last_keys))

def main():
    screen = urwid.curses_display.Screen()
    loop = urwid.MainLoop(TestWidget(), screen=screen)
    loop.run()

main()
