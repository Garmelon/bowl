from typing import Dict, Generic, Optional, TypeVar

from .element import Id, RenderedElement

__all__ = ["RenderedElementCache"]

E = TypeVar("E", bound=RenderedElement)

class RenderedElementCache(Generic[E]):

    def __init__(self) -> None:
        self._elements: Dict[Id, E] = {}

    def invalidate(self, elem_id: Id) -> None:
        try:
            self._elements.pop(elem_id)
        except KeyError:
            pass

    def invalidate_all(self) -> None:
        self._elements = {}

    def get(self, elem_id: Id) -> Optional[E]:
        return self._elements.get(elem_id)

    def add(self, elem: E) -> None:
        self._elements[elem.id] = elem
