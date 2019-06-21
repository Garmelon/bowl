import unicodedata

__all__ = ["ulen"]

# See http://www.unicode.org/reports/tr11/#ED7
#
# "In a broad sense, wide characters include W, F, and A (when in East Asian
# context), and narrow characters include N, Na, H, and A (when not in East
# Asian context)."
_WIDE = {"W", "F", "A"} # when in East Asian context
_NARROW = {"N", "Na", "H", "A"} # when not in East Asian context

def ulen(string: str, east_asian_context: bool = False) -> int:
    length = 0

    if east_asian_context:
        for char in string:
            if char in _WIDE:
                length += 2
            else:
                length += 1

    else:
        for char in string:
            if char in _NARROW:
                length += 1
            else:
                length += 2

    return length

# TODO unicode string splitting based on the same principle as above
