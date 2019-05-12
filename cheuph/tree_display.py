import collections
from typing import Any, List, Optional, Set

from .element import Element, Id, RenderedElement
from .element_supply import ElementSupply
from .exceptions import TreeException
from .markup import AttributedText
from .tree_list import TreeList

__all__ = ["TreeDisplay"]

class TreeDisplay:
    """
    This class renders elements from an ElementSupply to a list of lines, which
    can then be drawn onto a curses window. It maintains two "pointers" to
    specific messages: An anchor, which is used for scrolling, and a cursor,
    which highlights elements and can be used for interaction.

    ANCHOR

    The anchor is a message at a fixed vertical screen position. This position
    is called the anchor offset and it specifies the position of the first line
    of the anchor message relative to the top of the screen.

    A position of 0 would mean that the anchor is displayed at the top of the
    screen, where a position of (height - 1) would mean that only the first
    line of the anchor is displayed at the bottom of the screen (the rest is
    offscreen).

    If no anchor is set, any attempt to render will result in a blank screen
    (as if the room was empty) since the anchor is the point from which the
    TreeDisplay starts to render the tree(s).

    CURSOR

    The cursor is a highlighted message that is meant to be used for user
    interaction.

    The element that the cursor points to is passed highlighed=True in its
    render() method, whereas all other elements are passed highlighted=False.
    The cursor can also point to None (i. e. no message), in which case no
    element is highlighted.

    At the moment, the TreeDisplay contains no cursor movement code, so the
    user of the TreeDisplay has to implement their own by setting the cursor to
    the respective element id themselves. You might also want to set the anchor
    to the cursor and maybe center it on screen when the cursor is moved.

    RENDERING

    Rendering consists of these steps:

    0. Initialize the TreeDisplay with the correct screen width and height and
       keep the width and height up to date when the window resolution changes.
    1. Update the internal TreeList through one of various functions
    2. Cut out the display lines (the text that is later visible on screen)
    3. Draw the display lines to the curses window

    Step 2 uses the contents of the TreeList from step 1, but DOESN'T happen
    automatically when the TreeList changes. It is also guaranteed to not
    modify the display lines if it fails in some way.

    The display lines are supposed to contain the same text that is currently
    visible on the screen, and can be used to look up mouse clicks (see the
    "id" attribute in the "RENDERING - technical details" section below).
    They're a simple format for translating between elements and onscreen text.
    They are always as wide as the current width. Any missing characters are
    filled with spaces.

    RENDERING - technical details

    The process of rendering results in a TreeList and a list of lines (called
    display lines) representing the text that should be displayed on the
    screen.

    The TreeList's (vertical) offset of messages corresponds to the line on the
    screen where the message will be drawn. This means that the anchor
    message's offset in the TreeList will be the anchor offset referred to in
    the ANCHOR section above.

    Like the Elements and RenderedElements, the TreeDisplay and TreeList also
    use AttributedStrings for rendered content, especially in the display
    lines. In addition to the attributes added by the Element during rendering,
    the TreeDisplay also adds the following attributes to the display lines:

    1. "id" - the id of the element visible on this line
    2. "parent" - the parent id (or None) of the element visible on this line
    3. "cursor" - True, only added if the cursor points to the element visible
       on this line

    When an Element is rendered (producing a RenderedElement), its render()
    function is called with:
    1. the element's depth/level (top-level elements have a depth of 0)
    1. the current screen width
    2. whether the element is highlighted (by the cursor)
    3. whether the element is folded

    The RenderedElement contains one or more lines (zero lines may break the
    TreeDisplay, not sure yet) of AttributedText, which may contain formatting
    information (such as text color or style). This means that an Element can
    decide its own height.

    These lines should generally stay within the width passed to render(), but
    may exceed it in certain exceptional situations (e. g. too close to the
    right side of the screen). Because of this, the TreeDisplay supports
    horizontal scrolling.

    SCROLLING

    The most basic form of scrolling is to just increase or decrease the anchor
    offset. Depending on the application, this approach is enough. In some
    cases, more complex behaviour is required.

    For example, if you're displaying a section from a live tree structure like
    a chat room (see https://euphoria.io), there is no static top-most or
    bottom-most message to anchor to (unless you want to download the whole
    room's log). Also, new messages may appear at any time in (almost) any
    place.

    With the above, basic scrolling model, offscreen conversations would often
    slide around the visible messages, leading to frustration of the user. In
    cases like this, an alternative scrolling model can be employed:

    First, change the anchor offset as required and render the messages. Then,
    select the middle-most message as the new anchor and adapt the anchor
    offset such that the message stays in the same position.

    FOLDING

    Finally, the TreeDisplay supports folding and unfolding elements, making
    their subtrees invisible.

    Folding happens on elements. When an element is folded, it is still
    displayed but its (direct and indirect) child messages are no longer
    displayed.
    """

    def __init__(self,
            supply: ElementSupply,
            width: int,
            height: int,
            ) -> None:
        """
        supply - the ElementSupply that this TreeDisplay should use
        width  - the width of the target window (in characters)
        height - the width of the target window (in lines)

        To use the TreeDisplay, you might also want to:
        - set the anchor
        - make sure the anchor is visible
        """

        self.width = width
        self.height = height

        #self._root_id: Optional[Id] = None # TODO add root stuff

        self.anchor_id: Optional[Id] = None
        self.anchor_offset: int = 0

        self.cursor_id: Optional[Id] = None

        self.horizontal_offset: int = 0

        # Object references
        self._supply = supply
        self._folded: Set[Id] = set()

        self._rendered: Optional[TreeList] = None
        self._display_lines: Optional[List[AttributedText]] = None

    # RENDERING

    @property
    def display_lines(self) -> List[AttributedText]:
        if self._display_lines is None:
            raise TreeException((
                "No display lines available (have you called"
                " render_display_lines() yet?)"
            ))

        return self._display_lines

    def rerender(self) -> None:
        """
        This function updates the internal TreeList (step 1).

        It should be called when the ElementSupply changes or when the anchor,
        anchor offset, cursor, width or height are manually changed.
        """

        if self.anchor_id is None:
            # As described in the class docstring, we have no starting point
            # for rendering, so we don't even attempt it.
            self._rendered = None
            return

        anchor_tree = self._render_tree(self.anchor_id)

        self._rendered = TreeList(anchor_tree, self.anchor_id)
        self._rendered.offset_by(self.anchor_offset)

        self._fill_screen_upwards()
        self._fill_screen_downwards()

    def _render_tree(self,
            tree_id: Id,
            depth: int = 0
            ) -> List[RenderedElement]:

        elements: List[RenderedElement] = []

        highlighted = tree_id == self.cursor_id
        folded = tree_id in self._folded

        tree = self._supply.get(tree_id)
        rendered = tree.render(width=self.width, depth=depth,
            highlighted=highlighted, folded=folded)

        elements.append(rendered)

        if not folded:
            for child_id in self._supply.get_children_ids(tree_id):
                subelements = self._render_tree(child_id, depth=depth+1)
                elements.extend(subelements)

        return elements

    def _fill_screen_upwards(self) -> None:
        if self._rendered is None:
            raise TreeException((
                "Can't fill screen upwards without a TreeList. This exception"
                " should never occur."
            ))

        while True:
            if self._rendered.upper_offset <= 0:
                break

            above_tree_id = self._supply.get_previous_id(
                    self._rendered.upper_tree_id)

            if above_tree_id is None:
                break # We've hit the top of the supply

            self._rendered.add_above(self._render_tree(above_tree_id))

    def _fill_screen_downwards(self) -> None:
        """
        Eerily similar to _fill_screen_upwards()...
        """

        if self._rendered is None:
            raise TreeException((
                "Can't fill screen downwards without a TreeList. This exception"
                " should never occur."
            ))

        while True:
            if self._rendered.lower_offset >= self.height - 1:
                break

            below_tree_id = self._supply.get_next_id(
                    self._rendered.lower_tree_id)

            if below_tree_id is None:
                break # We've hit the bottom of the supply

            self._rendered.add_below(self._render_tree(below_tree_id))

    def render_display_lines(self) -> None:
        """
        This function updates the display lines (step 2).

        It should be called just before drawing the display lines to the curses
        window.
        """
        filler_line = AttributedText(" " * self.width)

        if self._rendered is None:
            self._display_lines = [filler_line] * self.height
            return

        lines = []

        if self._rendered.upper_offset > 0:
            # Fill the screen with empty lines until we hit the actual messages
            lines.extend([filler_line] * self._rendered.upper_offset)

        rendered_lines = self._rendered.to_lines(start=0, stop=self.height-1)
        lines.extend(line for line, rendered in rendered_lines)

        if self._rendered.lower_offset < self.height - 1:
            # Fill the rest of the screen with empty lines
            lines_left = self.height - 1 - self._rendered.lower_offset
            lines.extend([filler_line] * lines_left)

        self._display_lines = lines

    # SCROLLING

    def center_anchor(self) -> None:
        """
        Center the anchor vertically on the screen.

        This does not render anything.
        """

        pass # TODO

    def ensure_anchor_is_visible(self) -> None:
        """
        Scroll up or down far enough that the anchor is completely visible.

        If the anchor is higher than the screen, scroll such that the first
        line of the anchor is at the top of the screen.

        This does not render anything.
        """

        pass # TODO

    def anchor_center_element(self) -> None:
        """
        Select the element closest to the center of the screen (vertically) as
        anchor. Set the anchor offset such that no scrolling happens.

        This function updates the internal TreeList (step 1).
        """

        pass # TODO

    # FOLDING

    def is_folded(self, element_id: Id) -> bool:
        """
        Check whether an element is folded.

        This does not render anything.
        """

        return element_id in self._folded

    def fold(self, element_id: Id) -> None:
        """
        Fold an element.

        This does not render anything.
        """

        self._folded.add(element_id)

    def unfold(self, element_id: Id) -> None:
        """
        Unfold an element.

        This does not render anything.
        """

        if element_id in self._folded:
            self._folded.remove(element_id)

    def toggle_fold(self, element_id: Id) -> bool:
        """
        Toggle whether an element is folded.

        Returns whether the element is folded now.

        This does not render anything.
        """

        if self.is_folded(element_id):
            self.unfold(element_id)
            return False
        else:
            self.fold(element_id)
            return True

# Terminology:
#
# root
# ancestor
# parent
# sibling
# child
