"""Textual user interface for the Moonboard"""

import pandas as pd

from classification.hold_scores import get_hold_score
from settings import *


def visualise_holds_2016(start_holds, holds, finish_holds, highlight_holds=None) -> None:
    """Visualise holds on the Moonboard 2016 setup

    Only works for the 2016 setup, as the start and finish holds are not available on the 2017 setup.
    """
    if highlight_holds is None:
        highlight_holds = []
    start_color = '\033[92m'
    finish_color = '\033[91m'
    move_color = '\033[94m'
    highlight_color = "\033[93m"
    end_color = '\033[0m'

    hold_signs = [[" - " for _ in range(18)] for _ in range(11)]

    for hold_x, hold_y in start_holds:
        hold_signs[hold_x][hold_y] = start_color + " S " + end_color
    for hold_x, hold_y in holds:
        hold_signs[hold_x][hold_y] = move_color + " M " + end_color
    for hold_x, hold_y in finish_holds:
        hold_signs[hold_x][hold_y] = finish_color + " F " + end_color
    for hold_x, hold_y in highlight_holds:
        hold_signs[hold_x][hold_y] = highlight_color + " X " + end_color

    for index, hold_sign in pd.DataFrame(hold_signs).T.iloc[::-1].iterrows():
        print("".join(hold_sign))


def visualise_holds(holds, year=YEAR, board=BOARD) -> list:
    """Visualise holds on the Moonboard.

    Difficult holds are highlighted in red, normal holds in orange, and easy holds in green.
    """
    green_color = '\033[92m'
    yellow_color = "\033[93m"
    red_color = '\033[91m'
    end_color = '\033[0m'

    hold_signs = [["- " for _ in range(18)] for _ in range(11)]

    indexed_holds = list(enumerate(holds))

    for index, (hold_x, hold_y) in indexed_holds:
        hold_score = get_hold_score([hold_x, hold_y], year, board)

        # Adjust the color of a hold based on its difficulty
        if hold_score <= 0.5:
            move_color = green_color
        elif hold_score <= 0.75:
            move_color = yellow_color
        else:
            move_color = red_color

        # Make sure to print number centered if there are two digits
        if index < 10:
            hold_signs[hold_x][hold_y] = move_color + f"{index} " + end_color
        else:
            hold_signs[hold_x][hold_y] = move_color + f"{index}" + end_color

    print("   A B C D E F G H I J K")
    for index, hold_sign in pd.DataFrame(hold_signs).T.iloc[::-1].iterrows():
        index += 1
        if index < 10:
            print(f" {index} {''.join(hold_sign)}{index}")
        else:
            print(f"{index} {''.join(hold_sign)}{index}")
    print("   A B C D E F G H I J K")
    return indexed_holds


def main() -> None:
    """Main function, used for testing."""
    visualise_holds_2016([[0, 0], [5, 1]], [[4, 7], [6, 11], [1, 15]], [[3, 17]], [[6, 11]])
    visualise_holds([[0, 0], [5, 1], [4, 7], [6, 11], [1, 15], [3, 17]])


if __name__ == "__main__":
    main()
