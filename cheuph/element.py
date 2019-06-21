import datetime
from typing import Hashable, List, Optional

from .markup import AT

__all__ = ["Id", "Element", "RenderedElement", "Message", "RenderedMessage"]

Id = Hashable

class Element:

    def __init__(self,
            id: Id,
            parent_id: Optional[Id],
            ) -> None:

        self._id = id
        self._parent_id = parent_id

    @property
    def id(self) -> Id:
        return self._id

    @property
    def parent_id(self) -> Optional[Id]:
        return self._parent_id

class RenderedElement:

    def __init__(self, id: Id, lines: List[AT]) -> None:

        self._id = id
        self._lines = lines

    @property
    def id(self) -> Id:
        return self._id

    @property
    def lines(self) -> List[AT]:
        return self._lines

class Message(Element):

    def __init__(self,
            id: Id,
            parent_id: Optional[Id],
            timestamp: datetime.datetime,
            nick: str,
            content: str,
            ) -> None:

        super().__init__(id, parent_id)
        self._timestamp = timestamp
        self._nick = nick
        self._content = content

    @property
    def timestamp(self) -> datetime.datetime:
        return self._timestamp

    @property
    def nick(self) -> str:
        return self._nick

    @property
    def content(self) -> str:
        return self._content

class RenderedMessage(RenderedElement):

    def __init__(self, id: Id, lines: List[AT], meta: AT) -> None:
        super().__init__(id, lines)
        self._meta = meta

    @property
    def meta(self) -> AT:
        return self._meta
