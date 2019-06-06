from typing import Any, Iterable, List, Mapping, Optional, Tuple, Union

__all__ = ["Attributes", "Chunk", "AttributedText", "AT"]

Attributes = Mapping[str, Any]

# TODO remove empty Chunks in join_chunks
class Chunk:
    @staticmethod
    def join_chunks(chunks: List["Chunk"]) -> List["Chunk"]:
        if not chunks:
            return []

        new_chunks: List[Chunk] = []

        current_chunk = chunks[0]
        for chunk in chunks[1:]:
            joined_chunk = current_chunk._join(chunk)

            if joined_chunk is None:
                new_chunks.append(current_chunk)
                current_chunk = chunk
            else:
                current_chunk = joined_chunk

        new_chunks.append(current_chunk)

        return new_chunks

    # Common special methods

    def __init__(self,
            text: str,
            attributes: Attributes = {},
            ) -> None:
        self._text = text
        self._attributes = dict(attributes)

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"Chunk({self.text!r}, {self._attributes!r})"

    # Uncommon special methods

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Chunk):
            return NotImplemented

        return self._text == other._text and self._attributes == other._attributes

    def __getitem__(self, key: Union[int, slice]) -> "Chunk":
        return Chunk(self.text[key], self._attributes)

    def __len__(self) -> int:
        return len(self.text)

    # Properties

    @property
    def text(self) -> str:
        return self._text

    @property
    def attributes(self) -> Attributes:
        return dict(self._attributes)

    # Private methods

    def _join(self, chunk: "Chunk") -> Optional["Chunk"]:
        if self._attributes == chunk._attributes:
            return Chunk(self.text + chunk.text, self._attributes)

        return None

    # Public methods

    def get(self, name: str, default: Any = None) -> Any:
        return self.attributes.get(name, default)

    def set(self, name: str, value: Any) -> "Chunk":
        new_attributes = dict(self._attributes)
        new_attributes[name] = value
        return Chunk(self.text, new_attributes)

    def remove(self, name: str) -> "Chunk":
        new_attributes = dict(self._attributes)

        # This removes the value with that key, if it exists, and does nothing
        # if it doesn't exist. (Since we give a default value, no KeyError is
        # raised if the key isn't found.)
        new_attributes.pop(name, None)

        return Chunk(self.text, new_attributes)

class AttributedText:
    """
    Objects of this class are immutable and behave str-like. Supported
    operations are len, + and splicing.
    """

    @classmethod
    def from_chunks(cls, chunks: Iterable[Chunk]) -> "AttributedText":
        new = cls()
        new._chunks = Chunk.join_chunks(list(chunks))
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

        self._chunks: List[Chunk] = []
        if text is not None:
            self._chunks.append(Chunk(text, attributes=attributes))

    def __str__(self) -> str:
        return self.text

    def __repr__(self) -> str:
        return f"AttributedText.from_chunks({self._chunks!r})"

    # Uncommon special methods

    def __add__(self, other: "AttributedText") -> "AttributedText":
        return AttributedText.from_chunks(self._chunks + other._chunks)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, AttributedText):
                return NotImplemented

        return self._chunks == other._chunks

    def __getitem__(self, key: Union[int, slice]) -> "AttributedText":
        chunks: List[Chunk]

        if isinstance(key, slice):
            chunks = Chunk.join_chunks(self._slice(key))
        else:
            chunks = [self._at(key)]

        return AttributedText.from_chunks(chunks)

    def __len__(self) -> int:
        return sum(map(len, self._chunks))

    def __mul__(self, other: int) -> "AttributedText":
        if not isinstance(other, int):
            return NotImplemented

        return self.from_chunks(self.chunks * other)

    # Properties

    @property
    def text(self) -> str:
        return "".join(chunk.text for chunk in self._chunks)

    @property
    def chunks(self) -> List[Chunk]:
        return list(self._chunks)

    # Private methods

    def _at(self, key: int) -> Chunk:
        if key < 0:
            key = len(self) + key

        pos = 0
        for chunk in self._chunks:
            chunk_key = key - pos

            if 0 <= chunk_key < len(chunk):
                return chunk[chunk_key]

            pos += len(chunk)

        # We haven't found the chunk
        raise KeyError

    def _slice(self, key: slice) -> List[Chunk]:
        start, stop, step = key.start, key.stop, key.step

        if start is None:
            start = 0
        elif start < 0:
            start = len(self) + start

        if stop is None:
            stop = len(self)
        elif stop < 0:
            stop = len(self) + stop

        pos = 0 # cursor position
        resulting_chunks = []

        for chunk in self._chunks:
            chunk_start = start - pos
            chunk_stop = stop - pos

            offset: Optional[int] = None
            if step is not None:
                offset = (start - pos) % step

            if chunk_stop <= 0 or chunk_start >= len(chunk):
                pass
            elif chunk_start < 0 and chunk_stop > len(chunk):
                resulting_chunks.append(chunk[offset::step])
            elif chunk_start < 0:
                resulting_chunks.append(chunk[offset:chunk_stop:step])
            elif chunk_stop > len(chunk):
                resulting_chunks.append(chunk[chunk_start::step])
            else:
                resulting_chunks.append(chunk[chunk_start:chunk_stop:step])

            pos += len(chunk)

        return resulting_chunks

    # Public methods

    def at(self, pos: int) -> Attributes:
        return self._at(pos).attributes

    def get(self,
            pos: int,
            name: str,
            default: Any = None,
            ) -> Any:
        return self._at(pos).get(name, default)

    # "find all separate blocks with this property"
    def find_all(self, name: str) -> List[Tuple[Any, int, int]]:
        blocks = []
        pos = 0
        block = None

        for chunk in self._chunks:
            if name in chunk.attributes:
                attribute = chunk.attributes[name]
                start = pos
                stop = pos + len(chunk)

                if block is None:
                    block = (attribute, start, stop)
                    continue

                block_attr, block_start, _ = block

                if block_attr == attribute:
                    block = (attribute, block_start, stop)
                else:
                    blocks.append(block)
                    block = (attribute, start, stop)

            pos += len(chunk)

        if block is not None:
            blocks.append(block)

        return blocks

    def split_by(self, attribute_name: str) -> List[Tuple["AttributedText", Any]]:
        blocks = []

        chunks: List[Chunk] = []
        attribute: Any = None

        for chunk in self._chunks:
            chunk_attr = chunk.attributes.get(attribute_name)

            if chunks:
                if attribute == chunk_attr:
                    chunks.append(chunk)
                else:
                    blocks.append((self.from_chunks(chunks), attribute))

                    chunks = [chunk]
                    attribute = chunk_attr
            else:
                chunks.append(chunk)
                attribute = chunk_attr

        if chunks:
            blocks.append((self.from_chunks(chunks), attribute))

        return blocks

    def join(self, segments: Iterable["AttributedText"]) -> "AttributedText":
        # Lazy and inefficient solution to the fact that segments can be any
        # Iterable. TODO: Optimize, if this becomes a bottleneck.
        segments = list(segments)

        interspersed = segments[:1]
        for segment in segments[1:]:
            interspersed.append(self)
            interspersed.append(segment)

        chunks = []
        for segment in interspersed:
            chunks.extend(segment.chunks)

        return self.from_chunks(chunks)

    def set(self,
            name: str,
            value: Any,
            start: Optional[int] = None,
            stop: Optional[int] = None,
            ) -> "AttributedText":
        if start is None and stop is None:
            chunks = (chunk.set(name, value) for chunk in self._chunks)
            return AttributedText.from_chunks(chunks)
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
            chunks = (chunk.remove(name) for chunk in self._chunks)
            return AttributedText.from_chunks(chunks)
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
