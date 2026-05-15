"""Helper functions for moonboard operations."""

import numpy as np


def coordinate_letter_to_number(letter_coordinate) -> list:
    """Converts a letter coordinate to a number coordinate."""
    return [ord(letter_coordinate[0]) - 65, int(letter_coordinate[1:]) - 1]


def coordinate_number_to_letter(number_coordinate) -> str:
    """Converts a number coordinate to a letter coordinate."""
    return chr(number_coordinate[0] + 65) + str(number_coordinate[1] + 1)


def coordinate_center(left, right) -> list:
    """Returns the center coordinate between two holds."""
    return [np.mean([left[0], right[0]]), np.mean([left[1], right[1]])]


def coordinate_next_hold(left, right, next_hold, next_hand, moving_hand) -> list:
    """Returns the next hold coordinate based on the current holds and the next hand."""
    if moving_hand ^ (next_hand == "r"):
        result = [next_hold[0] - left[0], next_hold[1] - left[1]]
    else:
        result = [next_hold[0] - right[0], next_hold[1] - right[1]]
    if next_hand == "l":
        result[0] = -result[0]
    return result


def rotations_from_text(text) -> list:
    """Returns the rotations of a hold from a text string.

    The text string is a sequence of numbers separated by $. Each number represents a rotation. The rotations are
    returned as a list of directional vectors.
    """
    rotations = {
        0: [0., 1.],
        1: [.7, .7],
        2: [1., 0.],
        3: [.7, -.7],
        4: [0., -1.],
        5: [-.7, -.7],
        6: [-1., 0.],
        7: [-.7, .7]
    }
    return [rotations[int(x)] for x in text.split("$")]


def get_move_vectors(stationary_hold, moving_hold, next_hold) -> list:
    """Returns the x and y coordinates of each hand for a move."""
    n_s_x = next_hold[0] - stationary_hold[0]
    n_s_y = next_hold[1] - stationary_hold[1]
    n_m_x = next_hold[0] - moving_hold[0]
    n_m_y = next_hold[1] - moving_hold[1]
    return n_s_x, n_s_y, n_m_x, n_m_y


def get_vector_distance(x, y) -> float:
    """Returns the length of a vector."""
    return np.sqrt(np.power(x, 2) + np.power(y, 2))


def get_coordinate_distance(a, b) -> float:
    """Returns the distance between two coordinates."""
    return np.sqrt(np.power(a[0] - b[0], 2) + np.power(a[1] - b[1], 2))


def get_all_holds() -> list:
    """Returns a list of all hold coordinates."""
    return [[x, y] for x in range(11) for y in range(18)]


def main() -> None:
    """Main function, used for testing."""
    print(coordinate_letter_to_number("A1"))
    print(coordinate_letter_to_number("K18"))
    print(coordinate_number_to_letter([0, 0]))
    print(coordinate_number_to_letter([10, 17]))
    print(coordinate_number_to_letter(coordinate_letter_to_number("A1")) == "A1")
    print(coordinate_letter_to_number(coordinate_number_to_letter([0, 0])) == [0, 0])
    print(coordinate_center([0, 0], [1, 1]))
    print(coordinate_next_hold([-2, -2], [2, -2], [1, 1], "l", True))
    print(coordinate_next_hold([-2, -2], [2, -2], [1, 1], "r", True))
    print(coordinate_next_hold([-2, -2], [2, -2], [1, 1], "l", False))
    print(coordinate_next_hold([-2, -2], [2, -2], [1, 1], "r", False))
    print(rotations_from_text("0$1$2$3$4$5$6$7"))


if __name__ == "__main__":
    main()
