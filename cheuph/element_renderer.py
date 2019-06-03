from abc import ABC, abstractmethod
from typing import Generic, List, TypeVar

from .element import Element, RenderedElement, MetaRenderedElement
from .markup import AttributedText

__all__ = ["ElementRenderer"]

E = TypeVar("E", bound=Element)

class ElementRenderer(ABC, Generic[E]):
    """
    Knows how to render elements.
    """

    @abstractmethod
    def render(self, element: E, width: int) -> RenderedElement:
        pass
