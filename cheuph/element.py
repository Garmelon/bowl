import abc
from typing import Hashable, List, Optional

from .exceptions import ElementException, TreeException
from .markup import AttributedText

__all__ = ["Id", "Element", "RenderedElement"]

Id = Hashable

class Element(abc.ABC):
    def __init__(self,
            id: Id,
            parent_id: Optional[Id],
            children: Optional[List[Element]],
            ) -> None:
        self._id = id
        self._parent_id = id

        self._children = children

    @property
    def id(self) -> Id:
        return self._id

    @property
    def parent_id(self) -> Id:
        return self._parent_id

    @property
    def children(self) -> List[Element]:
        if self._children is None:
            raise ElementException("Element doesn't know its children")

        return self._children

    @children.setter
    def children(self, children: List[Element]) -> None:
        self._children = children

    @abc.abstractmethod
    def render(self,
            width: int,
            depth: int,
            highlighted: bool = False,
            folded: bool = False,
            ) -> RenderedElement:
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
    def lines(self) -> List[AttributedText]:
        return self._lines

    @property
    def height(self) -> int:
        return len(self._lines)
