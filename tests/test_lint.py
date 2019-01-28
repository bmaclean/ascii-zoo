import os

import pytest
from numpy.testing import assert_array_equal, assert_array_almost_equal

from game.animal import Animal
from lint.lint import parse_line, parse, create_animals, pin_groups_against_each_other, evenly_spaced_coords, \
    evenly_spaced_rects, shift_rects_to_center
from app_config import root_dir

# The directory that contains sample data for all tests
test_data_directory = os.path.join(root_dir, "tests/data")


def test_parse_line():
    result = parse_line("language/asciizoo.py:43: [E1120(no-value-for-parameter), ] "
                        "No value for argument 'repl' in function call")
    assert result["filepath"] == "language/asciizoo.py"
    assert result["line_number"] == 43
    assert result["error_category"] == "E"
    assert result["error_code"] == 1120
    assert result["error_string_code"] == "no-value-for-parameter"
    assert result["offending_object"] == ""
    assert result["offending_method"] == ""

    result = parse_line("language/asciizoo.py:43: [E1120(no-value-for-parameter), AttributeNode] "
                        "No value for argument 'repl' in function call")

    assert result["filepath"] == "language/asciizoo.py"
    assert result["line_number"] == 43
    assert result["error_category"] == "E"
    assert result["error_code"] == 1120
    assert result["error_string_code"] == "no-value-for-parameter"
    assert result["offending_object"] == "AttributeNode"
    assert result["offending_method"] == ""

    result = parse_line("language/asciizoo.py:43: [E1120(no-value-for-parameter), AttributeNode.parse] "
                        "No value for argument 'repl' in function call")

    assert result["filepath"] == "language/asciizoo.py"
    assert result["line_number"] == 43
    assert result["error_category"] == "E"
    assert result["error_code"] == 1120
    assert result["error_string_code"] == "no-value-for-parameter"
    assert result["offending_object"] == "AttributeNode"
    assert result["offending_method"] == "parse"


def test_parse():
    with open(os.path.join(test_data_directory, "pylint_output.txt")) as f:
        df = parse(f)
    assert len(df) == 10


def test_parse_complete():
    """Parse a full pylint output which includes lines that aren't actually pylint data, but just visual separators
    or something."""
    with open(os.path.join(test_data_directory, "pylint_output_complete.txt")) as f:
        df = parse(f)
    assert len(df) == 84


@pytest.mark.skip()
def test_get_groups():
    with open(os.path.join(test_data_directory, "pylint_output.txt")) as f:
        groups = group_errors(parse(f))

    # Sort the groups so we can do the assertions below
    groups = sorted(groups, key=lambda x: (x.offending_object, x.error_category))

    assert len(list(groups)) == 5

    assert groups[0].error_category == "C"
    assert groups[0].offending_object == "AttributeNode"
    assert groups[0].offending_method == ""

    assert groups[1].error_category == "C"
    assert groups[1].offending_object == "AttributeNode"
    assert groups[1].offending_method == "parse"

    assert groups[2].error_category == "W"
    assert groups[2].offending_object == "AttributeNode"
    assert groups[2].offending_method == "parse"

    assert groups[3].error_category == "C"
    assert groups[3].offending_object == "DefineNode"
    assert groups[3].offending_method == "parse"

    assert groups[4].error_category == "W"
    assert groups[4].offending_object == "DefineNode"
    assert groups[4].offending_method == "parse"


@pytest.mark.skip()
def test_group_errors_complete():
    """Parse a complete pylint output, exactly as you'd get if you ran pylint on the command line, and group the
    errors. This is just a smoke test to make sure nothing crashes."""
    with open(os.path.join(test_data_directory, "pylint_output_complete.txt")) as f:
        # Loop because group_errors might be a generator
        for _ in group_errors(parse(f)):
            pass


@pytest.mark.skip()
def test_create_animals():
    """Same as test_group_errors_complete except create the corresponding animals too."""
    with open(os.path.join(test_data_directory, "pylint_output.txt")) as f:
        # Should have 5 animals because the end result had 5 LintErrorGroups
        assert len(create_animals(group_errors(parse(f)))) == 5


@pytest.mark.skip()
def test_organize_animals():
    """Another massive smoke test"""
    with open(os.path.join(test_data_directory, "pylint_output_complete.txt")) as f:
        organize_animals(create_animals(group_errors(parse(f))))


def test_pin_groups_against_each_other():
    animal1 = Animal()
    animal2 = Animal()
    animal3 = Animal()
    group1 = [animal1, animal2]
    group2 = [animal3]
    pin_groups_against_each_other((group1, group2))

    assert animal1.eats == {animal3}
    assert animal2.eats == {animal3}

    assert animal3.eats == {animal1, animal2}

    assert animal1.wants_to_eat(animal3)
    assert animal2.wants_to_eat(animal3)

    assert animal3.wants_to_eat(animal1)
    assert animal3.wants_to_eat(animal2)

    assert not animal1.wants_to_eat(animal2)
    assert not animal2.wants_to_eat(animal1)


def test_evenly_spaced_coords():
    result = evenly_spaced_coords(4, 4, 4)
    assert_array_almost_equal(result[0], [1, 1])
    assert_array_almost_equal(result[1], [1, 3])
    assert_array_almost_equal(result[2], [3, 1])
    assert_array_almost_equal(result[3], [3, 3])


def test_evenly_spaced_rects():
    result = evenly_spaced_rects(1, 1, 4)
    assert_array_almost_equal(result[0], [0, 0])
    assert_array_almost_equal(result[1], [0, 1])
    assert_array_almost_equal(result[2], [1, 0])
    assert_array_almost_equal(result[3], [1, 1])

    result = evenly_spaced_rects(2, 2, 5)
    assert_array_almost_equal(result[0], [0, 0])
    assert_array_almost_equal(result[1], [0, 2])
    assert_array_almost_equal(result[2], [0, 4])
    assert_array_almost_equal(result[3], [2, 0])
    assert_array_almost_equal(result[4], [2, 2])


def test_shift_rect_to_center():
    result = shift_rects_to_center([[0, 0]], [10, 10], 4, 4)
    assert_array_almost_equal(result[0], [8, 8])
