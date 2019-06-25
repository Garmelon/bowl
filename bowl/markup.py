from typing import Any, Iterable, List, Mapping, Optional, Tuple, Union
from dataclasses import dataclass

__all__ = ["Attributes", "AttributedText", "AT"]

Attributes = Mapping[str, Any]

@dataclass
class Char:

    char: str
    attrs: Attributes

    def set(self, name: str, value: Any) -> "Char":
        new_attrs = dict(self.attrs)
        new_attrs[name] = value
        return Char(self.char, new_attrs)

    def remove(self, name: str) -> "Char":
        new_attrs = dict(self.attrs)

        # This removes the value with that key, if it exists, and does nothing
        # if it doesn't exist. (Since we give a default value, no KeyError is
        # raised if the key isn't found.)
        new_attrs.pop(name, None)

        return Char(self.char, new_attrs)

class AttributedText:
    """
    Objects of this class are immutable and behave str-like. Supported
    operations are len, + and splicing.
    """

    @classmethod
    def from_chars(cls, chars: Iterable[Char]) -> "AttributedText":
        new = cls()
        new._chars = list(chars)
        return new

    # Common special methods

    def __init__(self,
            text: Optional[str] = None,
            attributes: Attributes = {},
            **kwargs: Any,
            ) -> None:
        """
        text - the content of the AttributedText, omitting it results in the
          AttributedText equivalent to an empty string

        attributes - a dict of attributes that apply to the whole
          AttributedText

        **kwargs - all named arguments besides "attributes" are interpreted
          as attributes that override any options set in the "attributes" dict
        """

        attributes = dict(attributes)
        attributes.update(kwargs)

        self._chars: List[Char] = []
        for char in text or "":
            self._chars.append(Char(char, attributes))

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return "N/A"

    # Uncommon special methods

    def __add__(self, other: "AttributedText") -> "AttributedText":
        return AttributedText.from_chars(self._chars + other._chars)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AttributedText):
                return NotImplemented

        return self._chars == other._chars

    def __getitem__(self, key: Union[int, slice]) -> "AttributedText":
        chars: List[Char]

        if isinstance(key, slice):
            chars = self._chars[key]
        else:
            chars = [self._chars[key]]

        return AttributedText.from_chars(chars)

    def __len__(self) -> int:
        return len(self._chars)

    def __mul__(self, other: int) -> "AttributedText":
        if not isinstance(other, int):
            return NotImplemented

        return self.from_chars(self._chars * other)

    # Properties

    @property
    def text(self) -> str:
        return "".join(char.char for char in self._chars)

    @property
    def chars(self) -> List[Char]:
        return list(self._chars)

    # Public methods

    def at(self, pos: int) -> Attributes:
        return self._chars[pos].attrs

    def get(self,
            pos: int,
            name: str,
            default: Any = None,
            ) -> Any:

        return self.at(pos).get(name, default)

    def split_by(self,
            attribute_name: str,
            ) -> List[Tuple["AttributedText", Any]]:

        blocks = []

        chars: List[Char] = []
        attribute: Any = None

        for char in self._chars:
            char_attr = char.attrs.get(attribute_name)

            if chars:
                if attribute == char_attr:
                    chars.append(char)
                else:
                    blocks.append((self.from_chars(chars), attribute))

                    chars = [char]
                    attribute = char_attr
            else:
                chars.append(char)
                attribute = char_attr

        if chars:
            blocks.append((self.from_chars(chars), attribute))

        return blocks

    def join(self, segments: Iterable["AttributedText"]) -> "AttributedText":
        # Lazy and inefficient solution to the fact that segments can be any
        # Iterable. TODO: Optimize, if this becomes a bottleneck.
        segments = list(segments)

        interspersed = segments[:1]
        for segment in segments[1:]:
            interspersed.append(self)
            interspersed.append(segment)

        chars = []
        for segment in interspersed:
            chars.extend(segment.chars)

        return self.from_chars(chars)

    def set(self,
            name: str,
            value: Any,
            start: Optional[int] = None,
            stop: Optional[int] = None,
            ) -> "AttributedText":

        if start is None and stop is None:
            chars = (char.set(name, value) for char in self._chars)
            return AttributedText.from_chars(chars)
        elif start is None:
            return self[:stop].set(name, value) + self[stop:]
        elif stop is None:
            return self[:start] + self[start:].set(name, value)
        elif start > stop:
            # set value everywhere BUT the specified interval
            return self.set(name, value, stop=stop).set(name, value, start=start)
        else:
            middle = self[start:stop].set(name, value)
            return self[:start] + middle + self[stop:]

    def set_at(self, name: str, value: Any, pos: int) -> "AttributedText":
        return self.set(name, value, pos, pos + 1)

    def remove(self,
            name: str,
            start: Optional[int] = None,
            stop: Optional[int] = None,
            ) -> "AttributedText":

        if start is None and stop is None:
            chars = (char.remove(name) for char in self._chars)
            return AttributedText.from_chars(chars)
        elif start is None:
            return self[:stop].remove(name) + self[stop:]
        elif stop is None:
            return self[:start] + self[start:].remove(name)
        elif start > stop:
            # remove value everywhere BUT the specified interval
            return self.remove(name, stop=stop).remove(name, start=start)
        else:
            middle = self[start:stop].remove(name)
            return self[:start] + middle + self[stop:]

AT = AttributedText
