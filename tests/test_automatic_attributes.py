# pylint: disable=unused-variable


import pytest

from datafiles import datafile


@datafile('../tmp/{self.name}.yml', auto_attr=True, auto_save=False)
class Sample:
    name: str


def describe_auto_attr():
    @pytest.mark.flaky
    def with_builtin(expect, logbreak):
        sample = Sample('abc')

        sample.datafile.text = "count: 1"

        logbreak("Getting attribute")
        expect(sample.count) == 1

        logbreak("Setting attribute")
        sample.count = 4.2

        logbreak("Getting attribute")
        expect(sample.count) == 4

    @pytest.mark.flaky
    def with_empty_list(expect, logbreak):
        sample = Sample('abc')

        sample.datafile.text = "empty_items: []"

        logbreak("Getting attribute")
        expect(sample.empty_items) == []

        logbreak("Setting attribute")
        sample.empty_items.append(4.2)
        sample.empty_items.append("abc")

        logbreak("Getting attribute")
        expect(sample.empty_items) == [4.2, "abc"]

    @pytest.mark.flaky
    def with_homogeneous_list(expect, logbreak):
        sample = Sample('abc')

        sample.datafile.text = "same_items: [1, 2]"

        logbreak("Getting attribute")
        expect(sample.same_items) == [1, 2]

        logbreak("Setting attribute")
        sample.same_items.append(3.2)

        logbreak("Getting attribute")
        expect(sample.same_items) == [1, 2, 3]

    @pytest.mark.flaky
    def with_heterogeneous_list(expect, logbreak):
        sample = Sample('abc')

        sample.datafile.text = "mixed_items: [1, 'abc']"

        logbreak("Getting attribute")
        expect(sample.mixed_items) == [1, "abc"]

        logbreak("Setting attribute")
        sample.mixed_items.append(3.2)

        logbreak("Getting attribute")
        expect(sample.mixed_items) == [1, "abc", 3.2]

    @pytest.mark.flaky
    def with_dict(expect, logbreak):
        sample = Sample('abc')

        sample.datafile.text = "data: {'a': 1}"

        logbreak("Getting attribute")
        expect(sample.data) == {'a': 1}

        logbreak("Setting attribute")
        sample.data['b'] = 2.3

        logbreak("Getting attribute")
        expect(sample.data) == {'a': 1, 'b': 2.3}
