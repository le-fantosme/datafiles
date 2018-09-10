import dataclasses
import inspect
from pathlib import Path
from typing import Any, Dict, Optional

import log

from . import formats
from .converters import List
from .utils import cached


Missing = dataclasses._MISSING_TYPE  # pylint: disable=protected-access


class ModelManager:
    def __init__(self, cls):
        self.model = cls

    def all(self):
        raise NotImplementedError


class InstanceManager:
    def __init__(
        self, *, instance: Any, pattern: Optional[str], attrs: Dict
    ) -> None:
        self._instance = instance
        self._pattern = pattern
        self.attrs = attrs

    @property
    def path(self) -> Optional[Path]:
        return self._get_path()

    @cached
    def _get_path(self) -> Optional[Path]:
        if not self._pattern:
            log.debug(f'{self!r} has no path pattern')
            return None

        relpath = self._pattern.format(self=self._instance)
        root = Path(inspect.getfile(self._instance.__class__)).parent
        path = (root / relpath).resolve()
        log.info(f'Datafile path: {path}')
        return path

    @property
    def exists(self) -> bool:
        if not self.path:
            log.debug("'pattern' not set so datafile will never exist")
            return False

        result = self.path.exists()
        log.debug(f'Datafile exists: {result}')
        return result

    @property
    def data(self) -> Dict:
        return self._get_data()

    def _get_data(self, include_default_values=False) -> Dict:
        log.info(f'Preserializing object {self._instance!r} to data')

        data: Dict = dataclasses.asdict(self._instance)

        for name in list(data.keys()):
            if name not in self.attrs:
                log.debug(f'Removed unmapped attribute: {name}')
                data.pop(name)

        for name, converter in self.attrs.items():
            value = data[name]
            log.debug(
                f"Converting '{name}' value as {converter.__name__}: {value!r}"
            )

            if dataclasses.is_dataclass(converter):
                if value is None:
                    value = {}

                for field in dataclasses.fields(converter):
                    if field.name not in value:
                        log.debug(
                            f'Added missing nested attribute: {field.name}'
                        )
                        value[field.name] = None

                data[name] = converter(**value).datafile.data

            elif (
                value == self._get_default_field_value(name)
                and not include_default_values
            ):
                log.debug(f"Skipped default value for '{name}' attribute")
                data.pop(name)

            else:
                data[name] = converter.to_preserialization_data(value)

        log.info(f'Preserialized object data: {data}')
        return data

    @property
    def text(self) -> str:
        return self._get_text()

    def _get_text(self, include_default_values=False):
        extension = self.path.suffix if self.path else '.yml'
        log.info(f'Serializing data to text ({extension}): {self.data}')

        data = self._get_data(include_default_values=include_default_values)
        text = formats.serialize(data, extension)
        log.info(f'Serialized text ({extension}): {text!r}')

        return text

    def load(self, *, first_load=False) -> None:
        log.info(f'Loading values for {self._instance}')

        if not self.path:
            raise RuntimeError("'pattern' must be set to load the model")

        data = formats.deserialize(self.path, self.path.suffix)
        log.debug(f'Deserialized file data: {data}')

        for name, converter in self.attrs.items():
            log.debug(f"Converting '{name}' data to value")

            if dataclasses.is_dataclass(converter):
                self._set_container_value(data, name, converter, first_load)
            else:
                self._set_attribute_value(data, name, converter, first_load)

    def _set_container_value(self, data, name, converter, first_load):
        # TODO: Support nesting unlimited levels
        # https://github.com/jacebrowning/datafiles/issues/22
        data2 = data.get(name)
        if data2 is None:
            return

        log.debug(f'Converting nested data to Python: {data2}')

        value = getattr(self._instance, name)
        if value is None:
            for field in dataclasses.fields(converter):
                if field.name not in data2:  # type: ignore
                    data2[field.name] = None  # type: ignore
            value = converter(**data2)
        elif first_load:
            return

        manager2 = value.datafile
        for name2, converter2 in manager2.attrs.items():
            _value2 = data2.get(  # type: ignore
                # pylint: disable=protected-access
                name2,
                manager2._get_default_field_value(name2),
            )
            value2 = converter2.to_python_value(_value2)
            log.debug(f"'{name2}' as Python: {value2}")
            setattr(value, name2, value2)

        log.debug(f"Setting '{name}' value: {value!r}")
        setattr(self._instance, name, value)

    def _set_attribute_value(self, data, name, converter, first_load):
        file_value = data.get(name, Missing)
        init_value = getattr(self._instance, name)
        default_value = self._get_default_field_value(name)

        if first_load:
            log.debug(
                'First load values: file=%r, init=%r, default=%r',
                file_value,
                init_value,
                default_value,
            )

            if file_value == default_value:
                log.debug(
                    f"Ignored default '{name}' file value: {default_value!r}"
                )
                return

            if init_value != default_value and not issubclass(converter, List):
                log.debug(
                    f"Keeping non-default '{name}' init value: {init_value!r}"
                )
                return

        if file_value is Missing:
            if default_value is Missing:
                value = converter.to_python_value(None)
            else:
                value = converter.to_python_value(default_value)
        else:
            value = converter.to_python_value(file_value)

        log.info(f"Setting '{name}' value: {value!r}")
        setattr(self._instance, name, value)

    def _get_default_field_value(self, name):
        for field in dataclasses.fields(self._instance):
            if field.name == name:
                if not isinstance(field.default, Missing):
                    return field.default

                if not isinstance(
                    field.default_factory, Missing  # type: ignore
                ):
                    return field.default_factory()  # type: ignore

                if not field.init and hasattr(self._instance, '__post_init__'):
                    return getattr(self._instance, name)

        return Missing

    def save(self, include_default_values: bool = False) -> None:
        log.info(f'Saving data for {self._instance}')

        if not self.path:
            raise RuntimeError(f"'pattern' must be set to save the model")

        text = self._get_text(include_default_values=include_default_values)

        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(text)
