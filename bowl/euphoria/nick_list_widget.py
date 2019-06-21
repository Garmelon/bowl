from typing import List, Optional, Tuple

import urwid
import yaboli

from ..attributed_lines import AttributedLines
from ..attributed_lines_widget import AttributedLinesWidget
from ..markup import AT, Attributes

__all__ = ["NickListWidget"]

class NickListWidget(urwid.WidgetWrap):
    """
    This widget displays the nicks of the users currently connected to a Room.

    It must be notified of changes in the user list by the RoomWidget it is a
    part of.
    """

    def __init__(self,
            session: Optional[yaboli.Session] = None,
            users: Optional[yaboli.LiveSessionListing] = None,
            heading_attrs: Attributes = {},
            counter_attrs: Attributes = {},
            nick_attrs: Attributes = {},
            own_nick_attrs: Attributes = {},
            ) -> None:

        self._session = session
        self._users = users

        self._heading_attrs = heading_attrs
        self._counter_attrs = counter_attrs
        self._nick_attrs = nick_attrs
        self._own_nick_attrs = own_nick_attrs

        self._offset = 0
        self._lines = AttributedLinesWidget()

        super().__init__(self._lines)

        self.rerender()

    @property
    def session(self) -> Optional[yaboli.Session]:
        return self._session

    @session.setter
    def session(self, session: Optional[yaboli.Session]) -> None:
        self._session = session
        self.rerender()

    @property
    def users(self) -> Optional[yaboli.LiveSessionListing]:
        return self._users

    @users.setter
    def users(self, users: Optional[yaboli.LiveSessionListing]) -> None:
        self._users = users
        self.rerender()

    def _sort_users(self) -> Tuple[List[yaboli.Session], List[yaboli.Session], List[yaboli.Session], List[yaboli.Session]]:
        people = []
        bots = []
        lurkers = []
        nurkers = []

        users = [] if self._users is None else self._users.all

        if self.session is not None:
            users.append(self.session)

        for user in users:
            if user.nick:
                if user.is_bot:
                    bots.append(user)
                else:
                    people.append(user)
            else:
                if user.is_bot:
                    nurkers.append(user)
                else:
                    lurkers.append(user)

        return people, bots, lurkers, nurkers

    def _render_section(self,
            name: str,
            sessions: List[yaboli.Session],
            ) -> AttributedLines:

        lines = AttributedLines()

        sessions.sort(key=lambda sess: sess.nick)
        count = len(sessions)

        title = AT(name, attributes=self._heading_attrs)
        title += AT(f" ({count})", attributes=self._counter_attrs)
        lines.append_below({}, title)

        for sess in sessions:
            if not sess.nick:
                continue

            if sess is self._session:
                attributes = self._own_nick_attrs
            else:
                attributes = self._nick_attrs

            lines.append_below({}, AT(sess.nick, attributes=attributes))

        return lines

    def rerender(self) -> None:
        lines = AttributedLines()
        people, bots, lurkers, nurkers = self._sort_users()

        sections = []

        if people:
            sections.append(self._render_section("People", people))
        if bots:
            sections.append(self._render_section("Bots", bots))
        if lurkers:
            sections.append(self._render_section("Lurkers", lurkers))
        if nurkers:
            sections.append(self._render_section("Nurkers", nurkers))

        lines = AttributedLines()
        lines.upper_offset = self._lines.upper_offset

        if len(sections) < 1:
            lines.extend_below(self._render_section("Nobody", []))
        else:
            lines.extend_below(sections[0])
            for section in sections[1:]:
                lines.append_below({}, AT())
                lines.extend_below(section)

        self._lines.set_lines(lines)

    def scroll(self, delta: int) -> None:
        self._lines.upper_offset += delta

        self._lines.lower_offset = max(1, self._lines.lower_offset)
        self._lines.upper_offset = min(0, self._lines.upper_offset)

        self._invalidate()
