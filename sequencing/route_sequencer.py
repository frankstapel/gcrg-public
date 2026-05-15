from os.path import exists

import numpy as np

from helpers.files import *
from helpers.moonboard_gui import *
from helpers.moonboard_tui import *
from search import beam_search
from settings import *


def label_route_sequences(routes_df_file, sequence_folder, year=YEAR, board=BOARD) -> None:
    """Manually label the sequences for each route."""
    routes_df: pd.DataFrame = load_object(routes_df_file)

    for route_index, route in routes_df.iterrows():
        route_file = f"{sequence_folder}{year}_{board}_{route_index}.pkl"
        if exists(route_file):
            print(f"Route for path {route_file} has already been labeled.")
            continue

        print("==============\n")
        print(f"Route ID: {route_index}\n")
        print(f"Grade: {route['grade']}\n")
        visualise_route(route["moves"], route["grade"])
        indexed_holds = visualise_holds(route["moves"], year, board)
        hold_order = input("\nEnter hold order: ")
        print("")

        moves = []
        left = None
        right = None
        for hold in hold_order.split(" "):
            hand = hold[0].lower()
            index = int(hold[1:])

            if left is not None and right is not None:
                move = {
                    "left": indexed_holds[left][1],
                    "left_score": get_hold_score(indexed_holds[left][1], year, board),
                    "right": indexed_holds[right][1],
                    "right_score": get_hold_score(indexed_holds[right][1], year, board),
                    "next": indexed_holds[index][1],
                    "next_score": get_hold_score(indexed_holds[index][1], year, board),
                    "next_hand": hand,
                    "grade": route["grade"],
                    "normalized_grade": route["normalized_grade"]
                }
                moves.append(move)

            if hand == "l":
                left = index
            elif hand == "r":
                right = index
            else:
                print("Invalid sequence!\n")

        save_object(moves, route_file)


def create_sequences(routes_df_file, year=YEAR, board=BOARD, verbose=VERBOSE) -> None:
    """Use beam search to create sequences for each route."""
    routes_df: pd.DataFrame = load_object(routes_df_file)
    routes_df.reset_index(inplace=True)
    routes_df = routes_df.rename(columns={'index': 'route_index'})

    if verbose:
        print(routes_df)

    # Split routes_df into 10 chunks to parallelise
    routes_df_chunks = np.array_split(routes_df, 8)
    print(routes_df_chunks[0])

    index = input("Enter chunk index between [0, 7]: ")
    routes_df = routes_df_chunks[int(index)]

    routes_df["sequence"], routes_df["sequence_score"] = routes_df.apply(
        lambda route: beam_search(route.moves, route.route_index, 3, 5),
        axis=1, result_type='expand').transpose().values

    if verbose:
        print(routes_df)

    save_object(routes_df, f"../data/routes/{year}_{board}_sequenced_routes_{index}.pkl")


def combine_sequenced_routes(sequenced_routes_df_file, year=YEAR, board=BOARD, verbose=VERBOSE) -> None:
    """Combine the sequenced routes into one DataFrame."""
    sequenced_routes_df = pd.DataFrame()
    for index in range(8):
        sequenced_routes_df = sequenced_routes_df.append(
            load_object(f"../data/routes/{year}_{board}_sequenced_routes_{index}.pkl"))

    if verbose:
        print(sequenced_routes_df)

    save_object(sequenced_routes_df, sequenced_routes_df_file)


def main(label_sequences, combine_sequences) -> None:
    """Main function."""
    routes_df_file = f"../data/routes/{YEAR}_{BOARD}_routes.pkl"
    sequence_folder = "../data/sequences/"
    sequenced_routes_df_file = f"../data/routes/{YEAR}_{BOARD}_sequenced_routes.pkl"
    if label_sequences:
        label_route_sequences(routes_df_file, sequence_folder)
    create_sequences(routes_df_file)
    if combine_sequences:
        combine_sequenced_routes(sequenced_routes_df_file)


if __name__ == "__main__":
    main(False, False)
