__all__ = ["AttributedLinesWidget", "ALWidget"]

class AttributedLinesWidget:
    """
    This widget draws lines of AttributedText with a horizontal and a vertical
    offset. It can retrieve the attributes of any character by its (x, y)
    coordinates. Line-wide attributes may be specified.

    When clicked, it sends an event containing the attributes of the character
    that was just clicked.
    """

    pass

ALWidget = AttributedLinesWidget
