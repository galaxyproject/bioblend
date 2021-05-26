class InputsBuilder:
    """
    """

    def __init__(self):
        self._input_dict = {}

    def set(self, name, input):
        self._input_dict[name] = input
        return self

    def set_param(self, name, value):
        return self.set(name, param(value=value))

    def set_dataset_param(self, name, value, src="hda"):
        return self.set(name, dataset(value, src=src))

    def to_dict(self):
        values = {}
        for key, value in self.flat_iter():
            if hasattr(value, "value"):
                value = value.value
            values[key] = value
        return values

    def flat_iter(self, prefix=None):
        for key, value in self._input_dict.items():
            effective_key = key if prefix is None else f"{prefix}|{key}"
            if hasattr(value, "flat_iter"):
                yield from value.flat_iter(effective_key)
            else:
                yield effective_key, value


class RepeatBuilder:

    def __init__(self):
        self._instances = []

    def instance(self, inputs):
        self._instances.append(inputs)
        return self

    def flat_iter(self, prefix=None):
        for index, instance in enumerate(self._instances):
            index_prefix = f"{prefix}_{index}"
            yield from instance.flat_iter(index_prefix)


class Param:

    def __init__(self, value):
        self.value = value


class DatasetParam(Param):

    def __init__(self, value, src="hda"):
        if not isinstance(value, dict):
            value = dict(src=src, id=value)
        super().__init__(value)


inputs = InputsBuilder
repeat = RepeatBuilder
conditional = InputsBuilder
param = Param
dataset = DatasetParam

__all__ = ("inputs", "repeat", "conditional", "param")
