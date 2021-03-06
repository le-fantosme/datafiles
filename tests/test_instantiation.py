"""Tests for instantiating new synchronized objects."""

# pylint: disable=unused-variable

from dataclasses import dataclass, field

from datafiles import datafile


@datafile('../tmp/sample.yml', manual=True)
class SampleWithDefaults:
    foo: int = 1
    bar: str = 'a'


@dataclass
class NestedSample:
    name: str
    score: float


@datafile('../tmp/sample.yml', manual=True)
class SampleWithDefaultsAndNesting:
    nested: NestedSample
    name: str = ''
    score: float = 0.0


@datafile('../tmp/sample.yml', manual=True)
class SampleWithFactoryDefaults:
    a: float
    b: float
    c: float = field(default_factory=lambda: 42)


@datafile('../tmp/sample.yml', manual=True)
class SampleWithComputedDefaults:
    a: float
    b: float
    c: float = field(init=False)

    def __post_init__(self):
        self.c = self.a + self.b


def describe_existing_file():
    def it_wins_when_no_init_values(write, expect):
        write(
            'tmp/sample.yml',
            """
            foo: 2
            bar: b
            """,
        )

        sample = SampleWithDefaults()

        expect(sample.foo) == 2
        expect(sample.bar) == 'b'

    def it_loses_against_init_values(write, expect):
        write(
            'tmp/sample.yml',
            """
            foo: 3
            bar: c
            """,
        )

        sample = SampleWithDefaults(4, 'd')

        expect(sample.foo) == 4
        expect(sample.bar) == 'd'

    def it_wins_against_default_init_values(write, expect):
        write(
            'tmp/sample.yml',
            """
            bar: e
            """,
        )

        sample = SampleWithDefaults(foo=5)

        expect(sample.foo) == 5
        expect(sample.bar) == 'e'

    def it_merges_with_nested_value(write, expect):
        write(
            'tmp/sample.yml',
            """
            name: foo
            score: 7
            """,
        )

        sample = SampleWithDefaultsAndNesting(
            name='', score=0.0, nested=NestedSample(name='bar', score=8)
        )

        expect(sample.name) == 'foo'
        expect(sample.score) == 7.0
        expect(sample.nested.name) == 'bar'
        expect(sample.nested.score) == 8.0


def describe_factory_defaults():
    def when_no_file(expect):
        sample = SampleWithFactoryDefaults(1.2, 3.4)

        expect(sample.a) == 1.2
        expect(sample.b) == 3.4
        expect(sample.c) == 42.0

    def when_file_exists(write, expect):
        write(
            'tmp/sample.yml',
            """
            a: 1.0
            b: 2.0
            c: 9.9
            """,
        )

        sample = SampleWithFactoryDefaults(1.2, 3.4)

        expect(sample.a) == 1.2
        expect(sample.b) == 3.4
        expect(sample.c) == 9.9


def describe_computed_defaults():
    def when_no_file(expect):
        sample = SampleWithComputedDefaults(1.2, 3.4)

        expect(sample.a) == 1.2
        expect(sample.b) == 3.4
        expect(sample.c) == 4.6

    def when_file_exists(write, expect):
        write(
            'tmp/sample.yml',
            """
            a: 1.0
            b: 2.0
            c: 9.9
            """,
        )

        sample = SampleWithComputedDefaults(1.2, 3.4)

        expect(sample.a) == 1.2
        expect(sample.b) == 3.4
        expect(sample.c) == 9.9
