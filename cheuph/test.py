import curses
import subprocess
import tempfile
from typing import Any


def main(stdscr: Any) -> None:
    while True:
        key = stdscr.getkey()

        if key in {"\x1b", "q"}:
            return

        elif key == "e":
            with tempfile.TemporaryDirectory() as tmpdirname:
                tmpfilename = tmpdirname + "/" + "tempfile"
                #stdscr.addstr(f"{curses.COLOR_PAIRS!r}\n")
                stdscr.addstr(f"{tmpdirname!r} | {tmpfilename!r}\n")

                stdscr.getkey()

                curses.endwin()
                subprocess.run(["nvim", tmpfilename])
                stdscr.refresh()

                stdscr.getkey()

                with open(tmpfilename) as f:
                    for line in f:
                        stdscr.addstr(line)


curses.wrapper(main)
