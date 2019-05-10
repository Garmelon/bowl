import abc
from typing import Hashable, List, Optional

from .exceptions import ElementException, TreeException
from .markup import AttributedText

__all__ = ["Id", "Element", "ElementSupply", "RenderedElement"]

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
            depth: int,
            highlighted: bool,
            folded: bool,
            ) -> RenderedElement:
        pass

class ElementSupply(abc.ABC):
    @abc.abstractmethod
    def get(self, element_id: Id) -> Element:
        pass

    @abc.abstractmethod
    def get_parent_id(self, element_id: Id) -> Optional[Id]:
        pass

    def get_parent(self, element_id: Id) -> Optional[Element]:
        parent_id = self.get_parent_id(element_id)

        if parent_id is not None:
            return self.get(parent_id)
        else:
            return None

    @abc.abstractmethod
    def get_children_ids(self, element_id: Id) -> List[Id]:
        pass

    def get_children(self, element_id: Id) -> List[Element]:
        children_ids = self.get_children_ids(element_id)

        children: List[Element] = []
        for child_id in children_ids:
            children.append(self.get(child_id))

        return children

    # There is not a clear-cut way to get the previous or next "sibling" of an
    # element that is itself a child of the implicit root (None), since
    # get_children() doesn't accept None in its element_id argument.
    #
    # Because of this, the get_previous_id() and get_next_id() functions are
    # abstract (until I decide to change the signature of get_children(), that
    # is :P).

    @abc.abstractmethod
    def get_previous_id(self, element_id: Id) -> Optional[Id]:
        pass

    def get_previous(self, element_id: Id) -> Optional[Element]:
        previous_id = self.get_previous_id(element_id)

        if previous_id is not None:
            return self.get(previous_id)
        else:
            return None

    @abc.abstractmethod
    def get_next_id(self, element_id: Id) -> Optional[Id]:
        pass

    def get_next(self, element_id: Id) -> Optional[Element]:
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
                raise TreeException("Reached implicit root before hitting specified root")

            current_id = parent_id

    def get_furthest_ancestor(self,
            element_id: Id,
            root_id: Optional[Id] = None,
            ) -> Element:
        return self.get(self.get_furthest_ancestor_id(element_id,
            root_id=root_id))

    def get_tree(self, tree_id: Id) -> Element:
        tree = self.get(tree_id)

        children: List[Element] = []
        for child_id in self.get_children_ids(tree_id):
            children.append(self.get_tree(child_id))

        tree.children = children
        return tree

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
