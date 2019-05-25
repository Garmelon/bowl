__all__ = ["MessageTreeWidget"]

class MessageTreeWidget:
    """
    This widget displays an ElementSupply, including user interface like a
    cursor or folding markers. It usually is part of a RoomWidget. It also
    keeps a RenderedMessageCache (and maybe even other caches).

    It receives key presses and mouse clicks from its parent widget. It
    receives redraw requests and cache invalidation notices from the
    RoomWidget.

    It doesn't directly receive new messages. Rather, the RoomWidget adds them
    to the ElementSupply and then submits a cache invalidation notice and a
    redraw request.

    It emits a "room top hit" event (unnamed as of yet). When the RoomWidget
    receives this event, it should retrieve more messages from the server.

    It emits a "edit" event (unnamed as of yet) when the user attempts to edit
    a message. When the RoomWidget receives this event, it should open a text
    editor to compose a new message, and send that message once the user
    finishes editing it.
    """

    pass
