import collections
from typing import Deque, List, Optional, Tuple

from .element import Id, RenderedElement
from .markup import AttributedText

__all__ = ["TreeList"]

class TreeList:
    """
    This class is the stage between tree-like Element structures and lines of
    text like the TreeDisplay's DisplayLines.

    It keeps track of the results of rendering Element trees, and also the top
    and bottom tree's ids, so the TreeList can be expanded easily by appending
    trees to the top and bottom.

    Despite its name, the "trees" it stores are just flat lists, and they're
    stored in a flat deque one message at a time. Its name comes from how i is
    used with rendered Element trees.
    """

    def __init__(self,
            tree: List[RenderedElement],
            anchor_id: Id,
            ) -> None:
        self._deque: Deque[RenderedElement] = collections.deque()

        # The offsets can be thought of as the index of a line relative to the
        # anchor's first line.
        #
        # The upper offset is the index of the uppermost message's first line.
        # The lower offset is the index of the lowermost message's LAST line.
        self._upper_offset: int
        self._lower_offset: int

        # The upper and lower tree ids are the ids of the uppermost or
        # lowermost tree added to the TreeList. They can be used to request the
        # previous or next tree from an ElementSupply.
        self._upper_tree_id: Id
        self._lower_tree_id: Id

        self._add_first_tree(tree, anchor_id)

    @property
    def upper_offset(self) -> int:
        return self._upper_offset

    @property
    def lower_offset(self) -> int:
        return self._lower_offset

    @property
    def upper_tree_id(self) -> Id:
        return self._upper_tree_id

    @property
    def lower_tree_id(self) -> Id:
        return self._lower_tree_id

    def offset_by(self, delta: int) -> None:
        """
        Change all the TreeList's offsets by a delta (which is added to each
        offset).
        """

        self._upper_offset += delta
        self._lower_offset += delta

    def _add_first_tree(self,
            tree: List[RenderedElement],
            anchor_id: Id
            ) -> None:
        if len(tree) == 0:
            raise ValueError("The tree must contain at least one element")

        tree_id = tree[0].element.id
        self._upper_tree_id = tree_id
        self._lower_tree_id = tree_id

        offset = 0
        found_anchor = False

        for rendered in tree:
            if rendered.element.id == anchor_id:
                found_anchor = True
                self._upper_offset = -offset

            offset += rendered.height

        if not found_anchor:
            raise ValueError("The initial tree must contain the anchor")

        # Subtracting 1 because the lower offset is the index of the lowermost
        # message's last line, not the first line of a hypothetical message
        # below that.
        self._lower_offset = offset - 1

    def add_above(self, tree: List[RenderedElement]) -> None:
        """
        Add a rendered tree above all current trees.
        """

        if len(tree) == 0:
            raise ValueError("The tree must contain at least one element")

        self._upper_tree_id = tree[0].element.id

        for rendered in reversed(tree):
            self._deque.appendleft(rendered)
            self._upper_offset -= rendered.height

        # Alternative to the above for loop
        #delta = sum(map(lambda r: r.height, tree))
        #self._upper_offset -= delta
        #self._deque.extendLeft(reversed(tree))

    def add_below(self, tree: List[RenderedElement]) -> None:
        """
        Add a rendered tree below all current trees.
        """

        if len(tree) == 0:
            raise ValueError("The tree must contain at least one element")

        self._lower_tree_id = tree[0].element.id

        for rendered in tree:
            self._deque.append(rendered)
            self._lower_offset += rendered.height

        # Alternative to the above for loop
        #delta = sum(map(lambda r: r.height, tree))
        #self._lower_offset += delta
        #self._deque.extend(tree)

    def to_lines(self,
            start: Optional[int] = None,
            stop: Optional[int] = None,
            ) -> List[Tuple[AttributedText, RenderedElement]]:

        offset = self.upper_offset
        lines: List[Tuple[AttributedText, RenderedElement]] = []

        # I'm creating this generator instead of using two nested for loops
        # below, because I want to be able to break out of the for loop without
        # the code getting too ugly, and because it's fun :)
        all_lines = ((line, rendered)
                for rendered in self._deque
                for line in rendered.lines)

        for line, rendered in all_lines:
            after_start = start is not None and offset >= start
            before_stop = stop is not None and offset <= stop

            if after_start and before_stop:
                lines.append((line, rendered))

            if not before_stop:
                break

            offset += 1

        return lines
