__all__ = ["AttributedLines"]

class AttributedLines:
    """
    AttributedLines is a list of lines of AttributedText that maintains a
    vertical offset.

    When rendering a tree of messages, the RenderedMessage-s are drawn line by
    line to an AttributedLines. AttributedLines. The AttributedLines is then
    displayed in an AttributedLinesWidget.

    Multiple AttributedLines can be concatenated, keeping either the first or
    the second AttributedLines's offset.
    """

    pass
