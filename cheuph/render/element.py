from typing import Hashable, List

from .markup import AttributedText

__all__ = ["Id", "Element", "ElementSupply", "RenderedElement"]

Id = Hashable

class Element:
    pass

class ElementSupply:
    pass

class RenderedElement:
    def __init__(self,
            element: Element,
            rendered: List[AttributedText],
            ) -> None:
        self._element = element
        self._lines = rendered

    @property
    def element(self) -> Element:
        return self._element

    @property
    def height(self) -> int:
        return len(self._lines)
