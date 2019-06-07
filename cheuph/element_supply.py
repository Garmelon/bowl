from abc import ABC, abstractmethod
from typing import Dict, Generic, List, Optional, TypeVar

from .element import Element, Id

__all__ = ["ElementSupplyException", "ElementSupply", "InMemorySupply"]

class ElementSupplyException(Exception):
    pass

E = TypeVar("E", bound=Element)

class ElementSupply(ABC, Generic[E]):
    """
    An ElementSupply holds all of a room's known messages. It can be queried in
    different ways. Messages can also be added or removed from the supply as
    they are recived by the client.

    For example, a supply could store messages in memory, use a sqlite backend,
    or provide a caching layer above another supply.

    Naming convention:

    - All function parameters than end in "_id" are the id of an element
    - All functions that end in "_id" return the id of the element they're
      describing.
    - All functions that end in "_ids" return a list of ids of the elements
      they're describing.
    """

    @abstractmethod
    def get(self, elem_id: Id) -> E:
        """
        Retrieve a message by is id.
        """

        pass

    @abstractmethod
    def parent_id(self, elem_id: Id) -> Optional[Id]:
        """
        Retrieve an element's parent.

        Returns None if no parent exists.
        """

        pass

    @abstractmethod
    def child_ids(self, elem_id: Id) -> List[Id]:
        """
        Retrieve an element's children.
        """

        pass

    @abstractmethod
    def sibling_ids(self, elem_id: Id) -> List[Id]:
        """
        Retrieve an element's siblings.

        The list must always contain at least the id of the query element.
        """

        pass

    @abstractmethod
    def lowest_root_id(self) -> Optional[Id]:
        """
        Retrieve the lowest root element.

        A root element has no parent.
        """

        pass

    def root_id(self, elem_id: Id) -> Id:
        """
        Find the root of the tree that an element is contained in.
        """

        ancestor_id = elem_id

        while True:
            parent_id = self.parent_id(ancestor_id)
            if parent_id is None: break
            ancestor_id = parent_id

        return ancestor_id

    def previous_id(self, elem_id: Id) -> Optional[Id]:
        """
        Find an element's previous (upper) sibling.
        """

        sibling_ids = self.sibling_ids(elem_id)

        try:
            index = sibling_ids.index(elem_id)
            if index <= 0:
                return None
            else:
                return sibling_ids[index - 1]
        except ValueError:
            return None

    def next_id(self, elem_id: Id) -> Optional[Id]:
        """
        Find an element's next (lower) sibling.
        """

        sibling_ids = self.sibling_ids(elem_id)

        try:
            index = sibling_ids.index(elem_id)
            if index >= len(sibling_ids) - 1:
                return None
            else:
                return sibling_ids[index + 1]
        except ValueError:
            return None

class InMemorySupply(ElementSupply[E]):
    """
    This supply stores messages in memory. It orders the messages by their ids.
    """

    def __init__(self) -> None:
        self._elements: Dict[Id, E] = {}
        self._children: Dict[Id, List[Id]] = {}

    def add(self, elem: E) -> None:
        if elem.id in self._elements:
            self.remove(elem.id)

        self._elements[elem.id] = elem

        if elem.parent_id is not None:
            children = self._children.get(elem.parent_id, [])
            children.append(elem.id)
            children.sort()
            self._children[elem.parent_id] = children

    def remove(self, elem_id: Id) -> None:
        elem = self._elements.get(elem_id)
        if elem is None: return

        self._elements.pop(elem.id)

        if elem.parent_id is not None:
            children = self._children.get(elem.id)

            if children is not None: # just to satisfy mypy
                children.remove(elem)

                if not children:
                    self._children.pop(elem.id)

    def get(self, elem_id: Id) -> E:
        elem = self._elements.get(elem_id)

        if elem is None:
            raise ElementSupplyException(f"no element with id {elem_id!r}")

        return elem

    def child_ids(self, elem_id: Id) -> List[Id]:
        self.get(elem_id) # Throw exception if element doesn't exist

        return list(self._children.get(elem_id, []))

    def parent_id(self, elem_id: Id) -> Optional[Id]:
        elem = self.get(elem_id)
        return elem.parent_id

    def _roots(self) -> List[Id]:
        roots = (i for i, m in self._elements.items() if m.parent_id is None)
        return list(sorted(roots))

    def sibling_ids(self, elem_id: Id) -> List[Id]:
        parent_id = self.parent_id(elem_id)

        if parent_id is None:
            return self._roots()
        else:
            return self.child_ids(parent_id)

    def lowest_root_id(self) -> Optional[Id]:
        roots = self._roots()

        if roots:
            return roots[-1]
        else:
            return None
