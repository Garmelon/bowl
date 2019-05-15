import enum

__all__ = ["Style", "PALETTE"]

@enum.unique
class Style(enum.Enum):
    ROOM = "room"

PALETTE = [
    (Style.ROOM, "light blue,bold", ""),
]
