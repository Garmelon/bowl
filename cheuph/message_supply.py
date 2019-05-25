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

    pass
