from typing import Hashable, Optional

from .markup import AttributedText

__all__ = ["Message"]


class Message:
    def __init__(self,
            message_id: Hashable,
            parent_id: Optional[Hashable],
            author: str,
            content: str,
            ) -> None:
        self._message_id = message_id
        self._parent_id = parent_id
        self._author = author
        self._content = content

    @property
    def message_id(self) -> Hashable:
        return self._message_id

    @property
    def parent_id(self) -> Optional[Hashable]:
        return self._parent_id

    @property
    def author(self) -> str:
        return self._author

    @property
    def content(self) -> str:
        return self._content

    def render_content(self) -> AttributedText:
        return AttributedText(self.content)
