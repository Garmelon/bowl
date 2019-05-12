import curses
import subprocess
import tempfile
from typing import Any, List, Optional

from cheuph.element import Element, Id, RenderedElement
from cheuph.element_supply import MemoryElementSupply
from cheuph.markup import AttributedText
from cheuph.tree_display import TreeDisplay


class TestElement(Element):
    DEPTHSTR = "| "

    def __init__(self,
            id: Id,
            parent_id: Optional[Id],
            text: List[str],
            ) -> None:

        super().__init__(id, parent_id)
        self.text = text

    def render(self,
            width: int,
            depth: int,
            highlighted: bool = False,
            folded: bool = False,
            ) -> RenderedElement:

        depth_text = self.DEPTHSTR * depth
        lines = [f"{depth_text}{line}" for line in self.text]
        attributed_lines = [AttributedText(line) for line in lines]
        return RenderedElement(self, attributed_lines)

def main(stdscr: Any) -> None:
    messages = MemoryElementSupply()
    messages.add(TestElement("a", None, ["test element a"]))
    messages.add(TestElement("b", "a", ["test element b","child of a"]))
    messages.add(TestElement("c", None, ["test element c"]))

    display = TreeDisplay(messages, 80, 15)
    display.anchor_id = "a"
    display.anchor_offset = 5

    display.rerender()
    display.render_display_lines()

    print("-"*80)
    for line in display.display_lines:
        print(str(line))
    print("-"*80)

#    while True:
#        key = stdscr.getkey()
#
#        if key in {"\x1b", "q"}:
#            return
#
#        elif key == "e":
#            with tempfile.TemporaryDirectory() as tmpdirname:
#                tmpfilename = tmpdirname + "/" + "tempfile"
#                #stdscr.addstr(f"{curses.COLOR_PAIRS!r}\n")
#                stdscr.addstr(f"{tmpdirname!r} | {tmpfilename!r}\n")
#
#                stdscr.getkey()
#
#                curses.endwin()
#                subprocess.run(["nvim", tmpfilename])
#                stdscr.refresh()
#
#                stdscr.getkey()
#
#                with open(tmpfilename) as f:
#                    for line in f:
#                        stdscr.addstr(line)


#curses.wrapper(main)
main(None)
