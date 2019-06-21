from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

__all__ = ["ConfigException", "ConfigValueException", "TransparentConfig",
        "Kind", "Condition", "Option", "TreeLoader"]

class ConfigException(Exception):
    pass

class ConfigValueException(ConfigException):
    pass

class TransparentConfig:

    def __init__(self, parent: Optional["TransparentConfig"] = None) -> None:
        self.parent = parent

        self._values: Dict[str, Any] = {}

    def __getitem__(self, key: str) -> Any:
        return self.get(key)

    def __setitem__(self, key: str, value: Any) -> None:
        self.set(key, value)

    def get(self, name: str) -> Any:
        if name not in self._values:
            if self.parent is None:
                raise ConfigValueException(f"No such value: {name!r}")
            else:
                return self.parent.get(name)

        return self._values.get(name)

    def set(self, name: str, value: Any) -> None:
        self._values[name] = value

    def items(self) -> List[Tuple[str, Any]]:
        return list(self._values.items())

# Special config reading and writing classes

class Kind(Enum):

    BOOL = auto()
    DICT = auto()
    FLOAT = auto()
    INT = auto()
    STR = auto()
    RAW = auto()

    def matches(self, value: Any) -> bool:
        if   self == self.BOOL:  return type(value) is bool
        elif self == self.DICT:  return type(value) is dict
        elif self == self.FLOAT: return type(value) is float
        elif self == self.INT:   return type(value) is int
        elif self == self.STR:   return type(value) is str
        elif self == self.RAW:   return True

        return False

Condition = Callable[[Any], bool]

@dataclass
class Option:

    kind: Kind
    default: Any
    conditions: Iterable[Tuple[Condition, str]] = field(default_factory=list)

    def check_valid(self, value: Any) -> None:
        if not self.kind.matches(value):
            raise ConfigValueException(
                    f"value {value!r} does not match {self.kind}")

        self.apply_conditions(value)

    def apply_conditions(self, value: Any) -> None:
        for condition, error_message in self.conditions:
            if not condition(value):
                raise ConfigValueException(error_message)

class TreeLoader:

    def __init__(self) -> None:
        self._options: Dict[str, Any] = {}

    def add(self,
            name: str,
            kind: Kind,
            default: Any,
            *conditions: Tuple[Condition, str],
            ) -> None:

        option = Option(kind, default, conditions)
        self.add_option(name, option)

    def add_option(self, name: str, option: Option) -> None:
        self._options[name] = option

    def defaults(self) -> TransparentConfig:
        config = TransparentConfig()

        for name, option in self._options.items():
            config[name] = option.default

        return config

    def load_to(self, config: TransparentConfig, data: Any) -> None:
        errors = []

        for name, option in self._options.items():
            value = self._get_from_dict(data, name)
            if value is None: continue

            try:
                option.check_valid(value)
            except ConfigValueException as e:
                errors.append(f"{name}: {e}")
            else:
                config[name] = value

        if errors:
            raise ConfigValueException(errors)

    @classmethod
    def export(cls, config: TransparentConfig) -> Any:
        tree: Any = {}

        for key, value in config.items():
            cls._insert_into_dict(tree, key, value)

        return tree

    @staticmethod
    def _get_from_dict(d: Any, name: str) -> Optional[Any]:
        path = name.split(".")

        for segment in path:
            if d is None or type(d) is not dict:
                return None

            d = d.get(segment)

        return d

    @staticmethod
    def _insert_into_dict(d: Any, name: str, value: Any) -> None:
        path = name.split(".")
        if not path:
            raise ConfigException(f"could not insert value for {name}")

        for segment in path[:-1]:
            if type(d) is not dict:
                raise ConfigException(f"could not insert value for {name}")

            new_d = d.get(segment, {})
            d[segment] = new_d
            d = new_d

        if type(d) is not dict:
            raise ConfigException(f"could not insert value for {name}")

        d[path[-1]] = value
