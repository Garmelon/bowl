from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Generic, TypeVar

from .attributed_lines import AttributedLines
from .element import Element, Id
from .element_renderer import ElementRenderer
from .element_supply import ElementSupply

__all__ = ["ElementTreeRenderer", "CursorTreeRenderer"]

E = TypeVar("E", bound=Element)

class ElementTreeRenderer(ABC, Generic[E]):
    def __init__(self,
            supply: ElementSupply[E],
            renderer: ElementRenderer[E],
            ) -> None:
        self.supply = supply
        self.renderer = renderer

        self.lines = AttributedLines()

    @abstractmethod
    def rerender(self) -> None:
        pass

class CursorTreeRenderer(ElementTreeRenderer[E]):
    pass # TODO

#class HighlightTreeRenderer(ElementTreeRenderer[E]):
#    pass
