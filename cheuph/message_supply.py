import abc
from typing import Dict, List, Optional

from .exceptions import MessageSupplyException
from .message import Id, Message

__all__ = ["MessageSupply", "InMemoryMessageSupply"]


class MessageSupply(abc.ABC):
    """
    A MessageSupply holds all of a room's known messages. It can be queried in
    different ways. Messages can also be added to or removed from the MessageSupply
    as they are received by the client.

    The MessageSupply may use a database or keep messages in memory. A
    MessageSupply may also wrap around another MessageSupply, to provide caching or
    similar.
    """

    @abc.abstractmethod
    def get(self, message_id: Id) -> Message:
        pass

    @abc.abstractmethod
    def children_ids(self, message_id: Id) -> List[Id]:
        pass

    @abc.abstractmethod
    def sibling_ids(self, message_id: Id) -> List[Id]:
        pass

    @abc.abstractmethod
    def parent_id(self, message_id: Id) -> Optional[Id]:
        pass

    def oldest_ancestor_id(self, message_id: Id) -> Id:
        ancestor_id = message_id

        while True:
            parent_id = self.parent_id(ancestor_id)
            if parent_id is None: break
            ancestor_id = parent_id

        return ancestor_id

    def previous_id(self, message_id: Id) -> Optional[Id]:
        sibling_ids = self.sibling_ids(message_id)

        try:
            i = sibling_ids.index(message_id)
            if i <= 0:
                return None
            else:
                return sibling_ids[i - 1]
        except ValueError:
            return None

    def next_id(self, message_id: Id) -> Optional[Id]:
        sibling_ids = self.sibling_ids(message_id)

        try:
            i = sibling_ids.index(message_id)
            if i >= len(sibling_ids) - 1:
                return None
            else:
                return sibling_ids[i + 1]
        except ValueError:
            return None

    @abc.abstractmethod
    def lowest_root_id(self) -> Optional[Id]:
        pass

class InMemoryMessageSupply(MessageSupply):
    """
    This message supply stores messages in memory. It orders the messages by
    their ids.
    """

    def __init__(self) -> None:
        self._messages: Dict[Id, Message] = {}
        self._children: Dict[Id, List[Message]] = {}

    def add(self, message: Message) -> None:
        if message.id in self._messages:
            self.remove(message.id)

        self._messages[message.id] = message

        if message.parent_id is not None:
            children = self._children.get(message.parent_id, [])
            children.append(message)
            children.sort(key=lambda m: m.id)
            self._children[message.parent_id] = children

    def remove(self, message_id: Id) -> None:
        message = self._messages.get(message_id)
        if message is None: return

        self._messages.pop(message)

        if message.parent_id is not None:
            children = self._children.get(message.id)
            if children is not None: # just to satisfy mypy
                children.remove(message)

                if not children:
                    self._children.pop(message.id)

    def get(self, message_id: Id) -> Message:
        message = self._messages.get(message_id)

        if message is None:
            raise MessageSupplyException(
                    f"message with id {message_id!r} does not exist")

        return message

    def child_ids(self, message_id: Id) -> List[Id]:
        return [m.id for m in self._children.get(message_id, [])]

    def parent_id(self, message_id: Id) -> Optional[Id]:
        message = self.get(message_id)
        return message.parent_id

    def sibling_ids(self, message_id: Id) -> List[Id]:
        parent_id = self.parent_id(message_id)

        if parent_id is None:
            roots = [m for m in self._messages.values() if m.parent_id is None]
            sibling_ids = list(sorted(root.id for root in roots))
        else:
            sibling_ids = self.children_ids(parent_id)

        return sibling_ids

    def lowest_root_id(self) -> Optional[Id]:
        roots = list(sorted(self._messages.keys()))
        return roots[-1] if roots else None
