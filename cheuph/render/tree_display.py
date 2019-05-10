import collections
from typing import Any, List, Optional, Set

from .element import Element, ElementSupply, Id, RenderedElement
from .tree_list import TreeList

__all__ = ["TreeDisplay"]

class TreeDisplay:
    def __init__(self,
            supply: ElementSupply,
            width: int,
            height: int,
            ) -> None:
        self._width = width
        self._height = height

        self._root_id: Optional[Id] = None
        self._anchor_id: Optional[Id] = None
        self._cursor_id: Optional[Id] = None

        self._anchor_offset: int = 0
        self._horizontal_offset: int = 0

        # Object references
        self._supply = supply
        self._rendered: Optional[TreeList] = None
        self._folded: Set[Id] = set()

    def resize(self, width: int, height: int) -> None:
        # TODO maybe empty _rendered/invalidate caches etc.?
        self._width = width
        self._height = height

    def render(self) -> None:
        # Steps:
        #
        # 1. Find and render anchor's branch to TreeList
        # 2. Render above and below the branch until the screen is full (with
        #    the specified anchor offset)
        #   2.1. Keep the TreeList for later things like scrolling
        # 3. Cut out the visible lines and messages
        # 4. Cut out the visible parts horizontally (self._horizontal_offset)
        #   4.1. Keep the result for later reference (mouse clicks)
        # 5. Convert the result to plain text and draw it in the curses window
        #
        # Not happy with these steps yet. Scrolling, checking if the cursor is
        # in view, switching anchors etc. still feel weird.
        #
        # TODO Add the above into the TreeDisplay model.

        if self._anchor_id is None:
            return # TODO draw empty screen


        if self._root_id is None:
            ancestor_id = self._supply.get_furthest_ancestor_id(
                    self._anchor_id)
        else:
            ancestor_id = self._root_id

        ancestor_tree = self._render_tree(self._supply.get_tree(ancestor_id))

        self._rendered = TreeList(ancestor_tree, self._anchor_id)
        self._rendered.offset_by(self._anchor_offset)

        if self._root_id is None:
            self._fill_screen_upwards()
            self._fill_screen_downwards()

    def _render_tree(self,
            tree: Element,
            depth: int = 0
            ) -> List[RenderedElement]:
        elements: List[RenderedElement] = []

        highlighted = tree.id == self._cursor_id
        folded = tree.id in self._folded

        elements.append(tree.render(depth=depth, highlighted=highlighted,
            folded=folded))

        if not folded:
            for child in tree.children:
                elements.extend(self._render_tree(child, depth=depth+1))

        return elements

    def _fill_screen_upwards(self) -> None:
        if self._rendered is None:
            return # TODO

        while True:
            if self._rendered.upper_offset <= 0:
                break

            above_tree_id = self._supply.get_previous_id(
                    self._rendered.upper_tree_id)

            if above_tree_id is None:
                break

            above_tree = self._supply.get_tree(above_tree_id)
            self._rendered.add_above(self._render_tree(above_tree))

    def _fill_screen_downwards(self) -> None:
        """
        Eerily similar to _fill_screen_upwards()...
        """

        if self._rendered is None:
            return # TODO

        while True:
            if self._rendered.lower_offset >= self._height - 1:
                break

            below_tree_id = self._supply.get_next_id(
                    self._rendered.lower_tree_id)

            if below_tree_id is None:
                break

            below_tree = self._supply.get_tree(below_tree_id)
            self._rendered.add_below(self._render_tree(below_tree))

    def draw_to(self, window: Any) -> None:
        pass

# Terminology:
#
# root
# ancestor
# parent
# sibling
# child
