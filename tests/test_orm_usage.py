"""Tests that represent usage as an ORM."""

from dataclasses import dataclass

from datafiles import datafile


# This model is based on the example dataclass from:
# https://docs.python.org/3/library/dataclasses.html
@datafile('../tmp/inventory/{self.pk}.yml')
class InventoryItem:
    pk: int
    name: str
    unit_price: float
    quantity_on_hand: int = 0

    def total_cost(self) -> float:
        return self.unit_price * self.quantity_on_hand


def test_multiple_instances_are_distinct(expect, read, dedent):
    item_1 = InventoryItem(1, "Nuts", 0.23)
    item_2 = InventoryItem(2, "Bolts", 0.45, quantity_on_hand=100)

    expect(read('tmp/inventory/1.yml')) == dedent(
        """
        name: Nuts
        unit_price: 0.23
        """
    )
    expect(read('tmp/inventory/2.yml')) == dedent(
        """
        name: Bolts
        unit_price: 0.45
        quantity_on_hand: 100
        """
    )

    item_1.quantity_on_hand = 200
    item_2.unit_price = 0.34

    expect(read('tmp/inventory/1.yml')) == dedent(
        """
        name: Nuts
        unit_price: 0.23
        quantity_on_hand: 200
        """
    )
    expect(read('tmp/inventory/2.yml')) == dedent(
        """
        name: Bolts
        unit_price: 0.34
        quantity_on_hand: 100
        """
    )


def test_classes_can_share_a_nested_dataclass(logbreak, expect):
    @dataclass
    class Nested:
        value: int

    @datafile('../tmp/sample.json')
    class Foo:
        nested: Nested

    logbreak("Initialize Foo")
    foo = Foo(Nested(1))

    expect(foo.nested.value) == 1

    @datafile('../tmp/sample.toml')
    class Bar:
        nested: Nested

    logbreak("Initialize Bar")
    bar = Bar(Nested(2))

    expect(bar.nested.value) == 2


def test_unlimited_nesting(expect, read, dedent, write, logbreak):
    @dataclass
    class Bottom:
        level: int = 4

    @dataclass
    class C:
        level: int = 3
        d: Bottom = Bottom()

    @dataclass
    class B:
        level: int = 2
        c: C = C()

    @dataclass
    class A:
        level: int = 1
        b: B = B()

    @datafile('../tmp/sample.toml', defaults=True, auto_save=False)
    class Top:
        level: int = 0
        a: A = A()

    sample = Top()

    expect(read('tmp/sample.toml')) == dedent(
        """
        level = 0

        [a]
        level = 1

        [a.b]
        level = 2

        [a.b.c]
        level = 3

        [a.b.c.d]
        level = 4
        """
    )

    logbreak()
    sample.a.b.c.d.level = 99

    expect(read('tmp/sample.toml')) == dedent(
        """
        level = 0

        [a]
        level = 1

        [a.b]
        level = 2

        [a.b.c]
        level = 3

        [a.b.c.d]
        level = 99
        """
    )

    write(
        'tmp/sample.toml',
        """
        level = 0

        [a]
        level = 10

        [a.b]
        level = 20

        [a.b.c]
        level = 30

        [a.b.c.d]
        level = 40
        """,
    )

    logbreak()
    expect(sample.a.level) == 10
    expect(sample.a.b.level) == 20
    expect(sample.a.b.c.level) == 30
    expect(sample.a.b.c.d.level) == 40
