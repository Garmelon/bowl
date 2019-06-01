from typing import List, Optional

from .message import Id, Message

__all__ = ["MessageSupply"]


class MessageSupply:
    """
    A MessageSupply holds all of a room's known messages. It can be queried in
    different ways. Messages can also be added to or removed from the MessageSupply
    as they are received by the client.

    The MessageSupply may use a database or keep messages in memory. A
    MessageSupply may also wrap around another MessageSupply, to provide caching or
    similar.
    """

    # TODO should throw exception if it can't find the message
    def get(self, message_id: Id) -> Message:
        pass # TODO

    def children_ids(self, message_id: Id) -> List[Id]:
        pass # TODO

    def parent_id(self, message_id: Id) -> Optional[Id]:
        pass # TODO

    def oldest_ancestor_id(self, message_id: Id) -> Id:
        pass # TODO

    def previous_id(self, message_id: Id) -> Optional[Id]:
        pass # TODO

    def next_id(self, message_id: Id) -> Optional[Id]:
        pass # TODO

    def lowest_root_id(self) -> Optional[Id]:
        pass # TODO
