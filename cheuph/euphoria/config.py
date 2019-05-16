from typing import Any, Dict

__all__ = ["Fields", "Config", "ConfigView"]

Fields = Dict[str, Any]

class ConfigException(Exception):
    pass

class Config:
    @staticmethod
    def from_tree(tree: Any, prefix: str = "") -> Fields:
        """
        This function takes a nested dict using str-s as keys, and converts it
        to a flat Fields dict. This means that an option's value can't be a
        dict, and all dicts are expected to only use str-s as keys.

        It uses the '.' character as separator, so {"a":{"b": 1, "c": 2}}
        becomes {"a.b": 1, "a.c": 2}.
        """

        result: Fields = {}

        for k, v in tree.items():
            if not isinstance(k, str):
                raise ConfigException("Keys must be strings")

            if "." in k:
                raise ConfigException("Keys may not contain the '.' character")

            name = prefix + k

            if isinstance(v, dict):
                result.update(Config.from_tree(v, prefix=name+"."))
            else:
                result[name] = v

        return result

    @staticmethod
    def to_tree(fields: Fields) -> Fields:
        """
        This function does the opposite of from_tree().

        It uses the '.' character as separator, so {"a.b": 1, "a.c": 2}
        becomes {"a":{"b": 1, "c": 2}}.
        """

        result: Any = {}

        for k, v in fields.items():
            steps = k.split(".")

            subdict = result
            for step in steps[:-1]:
                new_subdict = subdict.get(step, {})
                subdict[step] = new_subdict
                subdict = new_subdict

            subdict[steps[-1]] = v

        return result

    def __init__(self, default_fields: Fields = {}) -> None:
        self.default_fields = default_fields
        self.fields: Fields = {}

    def __getitem__(self, key: str) -> Any:
        value = self.fields.get(key)

        if value is None:
            value = self.default_fields.get(key)

        if value is None:
            raise ConfigException(f"No value for {key} found")

        return value

    def __setitem__(self, key: str, value: Any) -> None:
        if isinstance(value, dict):
            raise ConfigException("No dicts allowed")
        default = self.default_fields.get(key)

        if value == default:
            if self.fields.get(key)is not None:
                self.fields.pop(key)
        else:
            self.fields[key] = value

    @property
    def view(self) -> "ConfigView":
        return ConfigView(
                self.to_tree(self.default_fields),
                self.to_tree(self.fields),
        )

class ConfigView:
    def __init__(self,
            default_fields: Any,
            fields: Any,
            prefix: str = "",
            ) -> None:

        self._default_fields = default_fields
        self._fields = fields
        self._prefix = prefix

    def __getattr__(self, name: str) -> Any:
        """
        This function assumes that _default_fields and _fields have the same
        dict structure.
        """

        default_field = self._default_fields.get(name)
        field = self._fields.get(name)

        if isinstance(field, dict) or isinstance(default_field, dict):
            # At least one is a dict, the other is either also a dict of the
            # same structure or None.
            default_field = default_field or {}
            field = field or {}

            return ConfigView(default_field, field, f"{self._prefix}{name}.")

        value = default_field if field is None else field

        if value is None:
            raise ConfigException(f"Field {self._prefix}{name} does not exist")

        return value
