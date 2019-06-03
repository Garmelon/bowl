from dataclasses import dataclass
from typing import Hashable, Optional

__all__ = ["Id", "Element", "RenderedElement"]

Id = Hashable

@dataclass
class Element:
    id: Id
    parent_id: Optional[Id]

@dataclass
class RenderedElement:
    id: Id
    meta: AttributedText
    lines: List[AttributedText]
