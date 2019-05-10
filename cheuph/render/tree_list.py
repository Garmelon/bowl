from .element import Id, RenderedElement

__all__ = ["TreeList"]

class TreeList:
    def __init__(self,
            tree: List[RenderedElement],
            anchor_id: Id,
            ) -> None:
        self._deque = collections.deque()

        self._anchor_id = anchor_id

        # The offsets can be thought of as the index of a line relative to the
        # anchor's first line.
        #
        # The upper offset is the index of the uppermost message's first line.
        # upper_offset <= 0.
        #
        # The lower offset is the index of the lowermost message's LAST line.
        # lower_offset >= 0.
        self._upper_offset: Int
        self._lower_offset: Int

        # The upper and lower tree ids are the ids of the uppermost or
        # lowermost tree added to the TreeList. They can be used to request the
        # previous or next tree from an ElementSupply.
        self._upper_tree_id: Id
        self._lower_tree_id: Id

        self._add_first_tree(tree)

    @property
    def upper_offset(self) -> Int:
        return self._upper_offset

    @property
    def lower_offset(self) -> Int:
        return self._lower_offset

    @property
    def upper_tree_id(self) -> Id:
        return self._upper_tree_id

    @property
    def lower_tree_id(self) -> Id:
        return self._lower_tree_id

    def _add_first_tree(self, tree: List[RenderedElement]) -> None:
        if len(tree) == 0:
            raise ValueError("The tree must contain at least one element")

        tree_id = tree[0].element.id
        self._upper_tree_id = tree_id
        self._lower_tree_id = tree_id

        offset = 0
        found_anchor = False

        for rendered in elements:
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
