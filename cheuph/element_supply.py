import abc
from typing import Dict, List, Optional, Set

from .element import Element, Id
from .exceptions import TreeException

__all__ = ["ElementSupply", "MemoryElementSupply"]

class ElementSupply(abc.ABC):
    """
    An ElementSupply is an interface to query some resource containing
    Elements. The elements could for example be kept in memory, in a database
    or somewhere else.

    The element ids must be unique, and the elements and their parents must
    form one or more trees (i. e. must not contain any cycles).
    """

    @abc.abstractmethod
    def get(self, element_id: Id) -> Element:
        """
        Get a single element by its id.
        """

        pass

    def get_parent_id(self, element_id: Id) -> Optional[Id]:
        """
        Get the id of the parent's element.

        This function is redundant, since you can just use element.parent_id.
        """

        return self.get(element_id).parent_id

    def get_parent(self, element_id: Id) -> Optional[Element]:
        """
        Like get_parent_id, but returns the Element instead.
        """

        parent_id = self.get_parent_id(element_id)

        if parent_id is not None:
            return self.get(parent_id)
        else:
            return None

    @abc.abstractmethod
    def get_children_ids(self, element_id: Optional[Id]) -> List[Id]:
        """
        Get a list of the ids of all the element's children.
        """

        pass

    def get_children(self, element_id: Optional[Id]) -> List[Element]:
        """
        Get a list of all children of an element.

        If the id passed is None, return a list of all top-level elements
        instead.
        """

        children_ids = self.get_children_ids(element_id)

        children: List[Element] = []
        for child_id in children_ids:
            children.append(self.get(child_id))

        return children

    def get_previous_id(self, element_id: Id) -> Optional[Id]:
        """
        Get the id of an element's previous sibling (i. e. the sibling just
        above it).

        Returns None if there is no previous sibling.

        Depending on the amount of elements in your ElementSupply, the default
        implementation might get very slow and/or use a lot of memory.
        """

        siblings = self.get_children_ids(self.get_parent_id(element_id))
        index = siblings.index(element_id)

        if index <= 0:
            return None
        else:
            return siblings[index - 1]

    def get_previous(self, element_id: Id) -> Optional[Element]:
        """
        Like get_previous_id(), but returns the Element instead.
        """

        previous_id = self.get_previous_id(element_id)

        if previous_id is not None:
            return self.get(previous_id)
        else:
            return None

    def get_next_id(self, element_id: Id) -> Optional[Id]:
        """
        Get the id of an element's next sibling (i. e. the sibling just below
        it).

        Returns None if there is no next sibling.

        Depending on the amount of elements in your ElementSupply, the default
        implementation might get very slow and/or use a lot of memory.
        """

        siblings = self.get_children_ids(self.get_parent_id(element_id))
        index = siblings.index(element_id)

        if index >= len(siblings) - 1:
            return None
        else:
            return siblings[index + 1]

    def get_next(self, element_id: Id) -> Optional[Element]:
        """
        Like get_next_id(), but returns the Element instead.
        """

        next_id = self.get_next_id(element_id)

        if next_id is not None:
            return self.get(next_id)
        else:
            return None

    def get_furthest_ancestor_id(self,
            element_id: Id,
            root_id: Optional[Id] = None,
            ) -> Id:
        current_id = element_id

        while True:
            parent_id = self.get_parent_id(current_id)

            if parent_id == root_id:
                return current_id
            elif parent_id is None:
                raise TreeException(
                    "Reached implicit root before hitting specified root")

            current_id = parent_id

    def get_furthest_ancestor(self,
            element_id: Id,
            root_id: Optional[Id] = None,
            ) -> Element:
        return self.get(self.get_furthest_ancestor_id(element_id,
            root_id=root_id))

class MemoryElementSupply(ElementSupply):
    """
    An in-memory implementation of an ElementSupply that works with any type of
    Element.
    """

    def __init__(self) -> None:
        self._elements: Dict[Id, Element] = {}
        self._children: Dict[Optional[Id], Set[Id]] = {None: set()}

    def add(self, element: Element) -> None:
        """
        Add a new element or overwrite an existing element with the same id.
        """

        if element.id in self._elements:
            self.remove(element.id)

        self._elements[element.id] = element
        self._children[element.id] = set()
        self._children[element.parent_id].add(element.id)

    def remove(self, element_id: Id) -> None:
        """
        Remove an element. This function does nothing if the element doesn't
        exist in this ElementSupply.
        """

        if element_id in self._elements:
            element = self.get(element_id)

            self._elements.pop(element_id)
            self._children.pop(element_id)
            self._children[element.parent_id].remove(element.id)

    def get(self, element_id: Id) -> Element:
        result = self._elements.get(element_id)

        if result is None:
            raise TreeException(f"Element with id {element_id!r} could not be found")

        return result

    def get_children_ids(self, element_id: Optional[Id]) -> List[Id]:
        result = self._children.get(element_id)

        if result is None:
            raise TreeException(f"Element with id {element_id!r} could not be found")

        return list(sorted(result))
