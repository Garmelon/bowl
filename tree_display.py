# Element supply of some sort
# Dict-/map-like
# Tree structure
# ↓
# List of already formatted elements
# Each with a line height, indentation, ...
# List structure
# ↓
# Messages and UI elements rendered to lines
# with meta-information, links/ids
# List structure, but on lines, not individual messages

class Element:
    pass

class ElementSupply:
    pass

class TreeDisplay:
    """
    Message line coordinates:

    n - Highest message
    ...
    1 - Higher message
    0 - Lowest message

    Screen/line coordinates:

    h-1 - First line
    h-2 - Second line
    ...
    1   - Second to last line
    0   - Last line

    Terms:

    <base>
    | ...
    | ... (above)
    | ...
    | <stem>
    | | ...
    | | | ... | <anchor>
    | ...
    | ... (below)
    | ...

    or

    <base>
    | ...
    | ... (above)
    | ...
    | <stem and anchor>
    | ...
    | ... (below)
    | ...

    The stem is a child of the base. The anchor is a direct or indirect child
    of the stem, or it is the stem itself.

    The base id may also be None (the implicit parent of all top-level
    messages in a room)
    """

    def __init__(self, window: Any) -> None:
        self.window = window

        self._anchor_id = None
        # Position of the formatted anchor's uppermost line on the screen
        self._anchor_screen_pos = 0


    def render(self) -> None:
        """
        Intermediate structures:
        - Upwards and downwards list of elements + focused element
        - Upwards and downwards list of rendered elements + focused element
        - List of visible lines (saved and used for mouse clicks etc.)

        Steps of rendering:
        1. Load all necessary elements
        2. Render all messages with indentation
        3. Compile lines

        Steps of advanced rendering:
        1. Load focused element + render
        2. Load tree of focused element + render
        3. Load trees above and below + render, as many as necessary
        4. While loading and rendering trees, auto-collapse
        5. Move focus if focused element was hidden in an auto-collapse
        ...?
        """

        # Step 1: Find and render the tree the anchor is in.

        stem_id = self._supply.find_stem_id(self._anchor_id,
                base=self._base_id)

        tree = self._supply.get_tree(stem_id)
        # The render might modify self._anchor_id, if the original anchor can't
        # be displayed.
        self._render_tree(tree)

        above, anchor, below = self._split_at_anchor(tree)

        # Step 2: Add more trees above and below, until the screen can be
        # filled or there aren't any elements left in the store.

        # h_win = 7
        # 6   | <- h_above = 3
        # 5   |
        # 4   |
        # 3 |  <- anchor, self._anchor_screen_pos = 3, anchor.height = 2
        # 2 |
        # 1   | <- h_below = 2
        # 0   |
        #
        # 7 - 3 - 1 = 3 -- correct
        # 3 - 2 + 1 = 2 -- correct

        height_window = None # TODO

        # All values are converted to zero indexed values in the calculations
        height_above = (height_window - 1) - self._anchor_screen_pos
        height_below = self._anchor_screen_pos - (anchor.height - 1)

        self._extend(above, height_above, base=self._base_id)
        self._extend(below, height_below, base=self._base_id)

        self._lines = self._render_to_lines(above, anchor, below)
        self._update_window(self._lines)

# TreeDisplay plan(s):
#
# [ ] 1. Render a basic tree thing from an ElementSupply
# [ ]   1.1. Take/own a curses window
# [ ]   1.2. Keep track of the text internally
# [ ]   1.3. Retrieve elements from an ElementSupply
# [ ]   1.4. Render elements to text depending on width of curses window
# [ ]   1.5. Do indentation
# [ ]   1.6. Use "..." where a thing can't be rendered
# [ ] 2. Scroll and anchor to messages
# [ ]   2.1. Listen to key presses
# [ ]   2.2. Scroll up/down single lines
# [ ]   2.3. Render starting from the anchor
# [ ]   2.4. Some sort of culling, but preserve CONSISTENCY!
# [ ] 3. Focus on single message
# [ ]   3.1. Keep track of focused message
# [ ]   3.2. Move focused message
# [ ]   3.3. Keep message visible on screen
# [ ]   3.4. Set anchor to focus when focus is visible
# [ ]   3.5. Find anchor solution for when focus is offscreen
# [ ] 4. Collapse element threads
# [ ]   4.1. Collapse thread at any element
# [ ]   4.2. Auto-collapse threads when they can't be displayed
# [ ]   4.3. Focus collapsed messages
# [ ]   4.4. Move focus when a hidden message would have focus
# [ ] 5. Interaction with elements
# [ ]   5.1. Forward key presses
# [ ]   5.2. Mouse clicks + message attributes
# [ ]   5.3. Element visibility
# [ ]   5.4. Request more elements when the top of the element supply is hit
# [ ]   5.5. ... and various other things

# STRUCTURE
#
# No async!
#
# The TreeView "owns" and completely fills one curses window.
#
# When rendering things, the TreeDisplay takes elements from the ElementSupply
# as needed. This should be a fast operation.
#
# When receiving key presses, the ones that are not interpreted by the TreeView
# are passed onto the currently focused element (if any).
#
# When receiving mouse clicks, the clicked-on element is focused and then the
# click and attributes of the clicked character are passed onto the focused
# element.
#
# (TODO: Notify focused elements? Make "viewed/new" state for elements
# possible?)
#
#
#
# DESIGN PRINCIPLES
#
# Layout: See below
#
# Color support: Definitely.
# No-color-mode: Not planned.
# => Colors required.

# The tree display can display a tree-like structure of elements.
#
# Each element consists of:
# 1. a way to display the element
# 2. a way to forward key presses to the element
# 3. element-specific attributes (Attributes), including:
#   3.1 "id", the element's hashable id
#   3.2 optionally "parent_id", the element's parent's hashable id
#
# (TODO: A way to notify the element that it is visible?)
#
# (TODO: Jump to unread messages, mark messages as read, up/down arrows like
# instant, message jump tags?)
#
# (TODO: Curses + threading/interaction etc.?)
#
#
#
# LAYOUT
#
# A tree display's basic structure is something like this:
#
# <element>
# | <element>
# | | <element>
# | | <element>
# | <element>
# | <element>
# | | <element>
# | | | <element>
# | <element>
# <element>
# | <element>
#
# It has an indentation string ("| " in the above example) that is prepended to
# each line according to its indentation. (TODO: Possibly add different types
# of indentation strings?)
#
# In general, "..." is inserted any time a message or other placeholder can't
# be displayed. (TODO: If "..." can't be displayed, it is shortened until it
# can be displayed?)
#
# Elements can be collapsed. Collapsed elements are displayed as "+ (<n>)"
# where <n> is the number of elements in the hidden subtree.
#
# If an element is so far right that it can't be displayed, the tree display
# first tries to collapse the tree. If the collapsed message can't be displayed
# either, it uses "..." as mentioned above.
#
# <element>
# | <element>
# | | <element>
# | | <element>
# | <element>
# | + (3)
# | <element>
# <element>
# | <element>
# | | <element>
# | | | <element>
# | | | | ...
#
#
#
# NAVIGATION
#
# For navigation, the following movements/keys are used (all other key presses
# are forwarded to the currently selected element, if there is one):
#
# LEFT (left arrow, h): move to the selected element's parent
#
# RIGHT (right arrow, l): move to the selected element's first child
#
# UP (up arrow, k): move to the element visually below the selected element
#
# DOWN (down arrow, j): move to the element visually above the selected element
#
# Mod + LEFT: move to the selected element's previous sibling, if one exists
#
# Mod + RIGHT: move to the selected element's next sibling, if one exists
#
# Mod + UP: scroll up by scroll step
#
# Mod + DOWN: scroll down by scroll step
#
#
# CURSES
#
# Main thread:
# - async
# - yaboli
# - curses: non-blocking input
# - curses: update visuals
# - run editor in async variant of subprocess or separate thread
#
#
#
# STRUCTURE
#
# ???
