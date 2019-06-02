import datetime
from dataclasses import dataclass
from typing import Hashable, List

from .attributed_lines import AttributedLines
from .markup import AT, AttributedText

__all__ = ["Id", "Message", "RenderedMessage"]


Id = Hashable


@dataclass
class Message:
    """
    A Message represents a single euphoria message. It contains the information
    and functionality necessary to render itself to lines of AttributedText.

    It does not contain information that usually changes, like a list of its
    child messages, or if it is currently folded.

    A message's content is assumed to never change. Truncated messages are
    never untruncated and displayed in full. Thus, the Message can ignore
    truncation status.
    """

    message_id: Id
    time: datetime.datetime
    nick: str
    content: str

    def render(self, width: int) -> "RenderedMessage":
        lines = self.content.split("\n")

        meta = AT(self.time.strftime("%H:%M "))

        nick = AT(f"[{self.nick}] ")
        nick_spaces = AT(" " * len(nick))

        result = []
        result.append(nick + AT(lines[0]))
        result.extend(nick_spaces + AT(line) for line in lines[1:])

        return RenderedMessage(self.message_id, meta, result)

@dataclass
class RenderedMessage:
    """
    A RenderedMessage is the result of rendering a Message. It contains lines
    of AttributedText, the target width to which the Message was rendered, its
    final dimensions and possibly some other useful information.

    It only contains the rendered sender nick and message body, NOT the
    message's indentation.

    A RenderedMessage is immutable. It can be used in a cache to prevent
    re-rendering each message every time it is needed (preventing word wrapping
    and other fancy calculations to be repeated on every re-render).

    It is also useful for scrolling and cursor movement, since the height of
    the message displayed on screen is not inherent to the Message object, but
    rather the result of rendering a Message.
    """

    message_id: Id
    meta: AttributedText
    lines: List[AttributedText]
