from datafiles import auto


def test_auto_with_sample_file(write, logbreak, expect, read, dedent):

    write(
        'tmp/sample.yml',
        """

        homogeneous_list:
        - 1
        - 2

        heterogeneous_list:
        - 1
        - 'abc'

        empty_list: []

        """,
    )

    logbreak("Inferring object")
    sample = auto('tmp/sample.yml')

    logbreak("Reading attributes")
    expect(sample.homogeneous_list) == [1, 2]
    expect(sample.heterogeneous_list) == [1, 'abc']
    expect(sample.empty_list) == []

    logbreak("Updating attribute")
    sample.homogeneous_list.append(3.4)
    sample.heterogeneous_list.append(5.6)
    sample.empty_list.append(7.8)

    logbreak("Reading file")
    expect(read('tmp/sample.yml')) == dedent(
        """

        homogeneous_list:
        - 1
        - 2
        - 3

        heterogeneous_list:
        - 1
        - abc
        - 5.6

        empty_list:
        - 7.8

        """
    )


def test_auto_with_real_files(expect):
    travis = auto('.travis.yml')
    expect(travis.language) == 'python'

    mkdocs = auto('mkdocs.yml')
    expect(mkdocs.theme) == 'readthedocs'
