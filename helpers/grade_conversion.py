"""Convert between different grading scales."""

FONT_GRADES = ["2", "3", "4", "4+", "5", "5+", "6A", "6A+", "6B", "6B+", "6C", "6C+", "7A", "7A+", "7B", "7B+", "7C",
               "7C+", "8A", "8A+", "8B", "8B+", "8C", "8C+"]
MOONBOARD_FONT_GRADES = ["6A+", "6B", "6B+", "6C", "6C+", "7A", "7A+", "7B", "7B+", "7C", "7C+", "8A", "8A+", "8B",
                         "8B+"]
USED_GRADES = ["6A+", "6B", "6B+", "6C", "6C+", "7A", "7A+", "7B", "7B+", "7C", "7C+"]


def font_to_ordinal(font_grade) -> list[int]:
    """ Create ordinal encoding for font grades so that they can be used in a regression model.

    Based on the article:
    https://12ft.io/proxy?&q=https%3A%2F%2Ftowardsdatascience.com%2Fsimple-trick-to-train-an-ordinal-regression-with-any-classifier-6911183d2a3c
    """
    font_grade = font_grade.strip().upper()
    conversion = {
        "6A+": [0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "6B": [1, 0, 0, 0, 0, 0, 0, 0, 0, 0],
        "6B+": [1, 1, 0, 0, 0, 0, 0, 0, 0, 0],
        "6C": [1, 1, 1, 0, 0, 0, 0, 0, 0, 0],
        "6C+": [1, 1, 1, 1, 0, 0, 0, 0, 0, 0],
        "7A": [1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        "7A+": [1, 1, 1, 1, 1, 1, 0, 0, 0, 0],
        "7B": [1, 1, 1, 1, 1, 1, 1, 0, 0, 0],
        "7B+": [1, 1, 1, 1, 1, 1, 1, 1, 0, 0],
        "7C": [1, 1, 1, 1, 1, 1, 1, 1, 1, 0],
        "7C+": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "8A": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "8A+": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "8B": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1],
        "8B+": [1, 1, 1, 1, 1, 1, 1, 1, 1, 1]
    }
    return conversion[font_grade]


def font_to_one_hot(font_grade) -> list[int]:
    """Convert font grade to one hot encoding."""
    font_grade = font_grade.strip().upper()
    one_hot = [0] * len(USED_GRADES)
    one_hot[USED_GRADES.index(font_grade)] = 1
    return one_hot


def one_hot_to_font(one_hot) -> str:
    """Convert one hot encoding to font grade."""
    return USED_GRADES[one_hot.index(1)]


def ordinal_probabilities_to_font(ordinal_probabilities) -> str:
    """Convert ordinal probabilities to font grade."""
    probabilities = {
        "6A+": 1.0 - ordinal_probabilities[0],
        "6B": ordinal_probabilities[0] - ordinal_probabilities[1],
        "6B+": ordinal_probabilities[1] - ordinal_probabilities[2],
        "6C": ordinal_probabilities[2] - ordinal_probabilities[3],
        "6C+": ordinal_probabilities[3] - ordinal_probabilities[4],
        "7A": ordinal_probabilities[4] - ordinal_probabilities[5],
        "7A+": ordinal_probabilities[5] - ordinal_probabilities[6],
        "7B": ordinal_probabilities[6] - ordinal_probabilities[7],
        "7B+": ordinal_probabilities[7] - ordinal_probabilities[8],
        "7C": ordinal_probabilities[8] - ordinal_probabilities[9],
        "7C+": ordinal_probabilities[9]
    }
    # Find the key of the highest probability
    return max(probabilities, key=probabilities.get)


def font_equals(font_grade1, font_grade2) -> bool:
    """Check if two font grades are equal."""
    return font_grade1.strip().upper() == font_grade2.strip().upper()


def font_one_off(font_grade1, font_grade2) -> bool:
    """Check if two font grades are within one off."""
    font_grade1 = font_grade1.strip().upper()
    font_grade2 = font_grade2.strip().upper()
    return abs(FONT_GRADES.index(font_grade1) - FONT_GRADES.index(font_grade2)) <= 1


def font_n_off(font_grade1, font_grade2, n) -> bool:
    """Check if two font grades are within n off."""
    font_grade1 = font_grade1.strip().upper()
    font_grade2 = font_grade2.strip().upper()
    return abs(FONT_GRADES.index(font_grade1) - FONT_GRADES.index(font_grade2)) <= n


def font_to_ircra(font_grade) -> int:
    """Convert font grade to IRCRA grade."""
    font_grade = font_grade.strip().upper()
    conversion = {
        "2": 9.0,
        "3": 11.0,
        "4": 12.0,
        "4+": 13.0,
        "5": 14.0,
        "5+": 15.0,
        "6A": 15.5,
        "6A+": 16.5,
        "6B": 17.0,
        "6B+": 18.0,
        "6C": 18.5,
        "6C+": 19.5,
        "7A": 20.5,
        "7A+": 21.5,
        "7B": 22.5,
        "7B+": 23.5,
        "7C": 24.5,
        "7C+": 25.5,
        "8A": 26.5,
        "8A+": 27.5,
        "8B": 28.5,
        "8B+": 29.5,
        "8C": 31.0,
        "8C+": 32.0
    }
    return conversion[font_grade]


def font_to_index(font_grade) -> int:
    """Convert font grade to index."""
    font_grade = font_grade.strip().upper()
    return FONT_GRADES.index(font_grade)


def index_to_font(index) -> str:
    """Convert index to font grade."""
    return FONT_GRADES[index]


def main() -> None:
    """Main function, used for testing."""
    print(font_to_ircra("2"))
    print(font_to_ircra("5+"))
    print(font_to_ircra("7a+"))
    print(ordinal_probabilities_to_font([0.95, 0.9, 0.8, 0.7, 0.6, 0.5, 0.4, 0.0, 0.0, 0.0, 0.0]))


if __name__ == "__main__":
    main()
