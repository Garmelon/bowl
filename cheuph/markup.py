from typing import Any, Dict, List, Optional, Union

__all__ = ["Attributes", "Chunk", "MarkedUp"]


Attributes = Dict[str, Any]


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

    def __getitem__(self, key: Union[int, slice]) -> "Chunk":
        return Chunk(self.text[key], self._attributes)

    def __len__(self) -> int:
        return len(self.text)

    # Properties

    @property
    def text(self) -> str:
        return self._text

    @property
    def attrs(self) -> Attributes:
        return dict(self._attributes)

    # Private methods

    def _join(self, chunk: "Chunk") -> Optional["Chunk"]:
        if self._attributes == chunk._attributes:
            return Chunk(self.text + chunk.text, self._attributes)
        else:
            return None

    # Public methods

    def with_attribute(self, name: str, value: Any) -> "Chunk":
        new_attributes = dict(self._attributes)
        new_attributes[name] = value
        return Chunk(self.text, new_attributes)

    def without_attribute(self, name: str) -> "Chunk":
        new_attributes = dict(self._attributes)

        # This removes the value with that key, if it exists, and does nothing
        # if it doesn't exist. (Since we give a default value, no KeyError is
        # raised if the key isn't found.)
        new_attributes.pop(name, None)

        return Chunk(self.text, new_attributes)


class MarkedUp:
    """
    Objects of this class are immutable and behave str-like. Supported
    operations are len, + and splicing.
    """

    @classmethod
    def from_chunks(cls, chunks: List[Chunk]) -> "MarkedUp":
        new = cls()
        new._chunks = Chunk.join_chunks(chunks)
        return new

    # Common special methods

    def __init__(self, text: Optional[str] = None) -> None:
        self._chunks: List[Chunk] = []
        if text is not None:
            self._chunks.append(Chunk(text))

    def __str__(self) -> str:
        return "".join(map(str, self._chunks))

    def __repr__(self) -> str:
        return f"MarkedUp.from_chunks({self._chunks!r})"

    # Uncommon special methods

    def __add__(self, other: "MarkedUp") -> "MarkedUp":
        return MarkedUp.from_chunks(self._pieces + other._pieces)

    def __getitem__(self, key: Union[int, slice]) -> "MarkedUp":
        chunks: List[Chunk]

        if isinstance(key, slice):
            chunks = Chunk.join_chunks(self._slice(key))
        else:
            chunks = [self._at(key)]

        return MarkedUp.from_chunks(chunks)

    def __len__(self) -> int:
        return sum(map(len, self._chunks))

    # Properties

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
        else:
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

    def attrs(self, key: int) -> Attributes:
        return self._at(key).attrs
