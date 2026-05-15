"""Prepare scraped data, create a routes dataframe and calculate hold scores."""

import glob
import os
import plotly.express as px

from helpers.files import *
from helpers.grade_conversion import *
from helpers.moonboard import *
from helpers.moonboard_gui import *
from settings import *


def find_scrape_file(year: str, board: str) -> str:
    """Find the route data file for the given year and board.
    
    Looks for files matching the pattern: {year}_{board}.*
    Supports both .json and .pkl formats.
    
    Args:
        year: Data year (e.g., "2016")
        board: Board name (e.g., "moonboard")
    
    Returns:
        Path to the data file
    
    Raises:
        FileNotFoundError: If no matching data file is found
    """
    # Try to find files matching the pattern
    data_dir = "../data/routes_input"
    pattern = os.path.join(data_dir, f"{year}_{board}.*")
    matches = glob.glob(pattern)
    
    if matches:
        return matches[0]
    
    # If not found, raise an error with helpful message
    raise FileNotFoundError(
        f"Could not find data file for {year} {board}.\n"
        f"Expected file: data/routes_input/{year}_{board}.json or .pkl\n"
        f"Supported formats: .json, .pkl\n"
        f"See DATA.md for format specifications."
    )



def prepare_routes_df(scrape_file, routes_df_file, verbose=VERBOSE) -> None:
    """Prepare a routes dataframe from a scrape file."""
    # Load the scrape file
    scrape_file_type = scrape_file.split(".")[-1]
    if scrape_file_type == "json":
        routes_df = pd.read_json(scrape_file)
        routes_df = routes_df.rename(columns={"Grade": "grade", "Moves": "moves"})
        routes_df["moves"] = routes_df["moves"].apply(lambda x: [coordinate_letter_to_number(move) for move in x])
    else:
        routes_df = pd.DataFrame.from_dict(load_object(scrape_file), orient="index")
        routes_df["moves"] = routes_df["start"] + routes_df["mid"] + routes_df["end"]

    print(routes_df)

    # Select the features to use
    routes_df = routes_df[["grade", "moves"]]
    routes_df = routes_df.reset_index(drop=True)
    routes_df["route_length"] = routes_df["moves"].map(len)

    print(len(routes_df))

    # Remove routes that contain the hold [0, 4] as this does not exist on the MoonBoard
    if scrape_file_type != "json":
        routes_df = routes_df[routes_df["moves"].apply(lambda x: [0, 5] not in x)]

    print(len(routes_df))

    # Remove duplicates
    routes_df["moves_string"] = routes_df.apply(
        lambda x: " - ".join([str(move[0]) + ":" + str(move[1]) for move in sorted(x.moves)]), axis=1)
    if verbose:
        print(f"Before removing duplicates: {len(routes_df)}")
        print(f"Removed {len(routes_df['moves_string']) - len(routes_df['moves_string'].drop_duplicates())} duplicates")
        print(f"After removing duplicates: {len(routes_df['moves_string'].drop_duplicates())}")
    routes_df = routes_df.drop_duplicates(subset=["moves_string"])

    # Convert the Font grades to the ordinal encoding
    routes_df["ordinal_grade"] = routes_df["grade"].apply(font_to_ordinal)

    # Convert the Font grades to the IRCRA scale.
    routes_df["IRCRA_grade"] = routes_df["grade"].apply(font_to_ircra)
    min_ircra_grade = np.min(routes_df["IRCRA_grade"])
    max_ircra_grade = np.max(routes_df["IRCRA_grade"])

    # Normalize the IRCRA grade to [0, 1].
    routes_df["normalized_IRCRA_grade"] = (routes_df["IRCRA_grade"] - min_ircra_grade) / (
            max_ircra_grade - min_ircra_grade)

    # Retrieve Font indices
    routes_df["font_index"] = routes_df["grade"].apply(font_to_index)
    min_font_index = np.min(routes_df["font_index"])
    max_font_index = np.max(routes_df["font_index"])

    # Normalize the IRCRA grade to [0, 1].
    routes_df["normalized_grade"] = (routes_df["font_index"] - min_font_index) / (
            max_font_index - min_font_index)

    # Save the routes dataframe
    save_object(routes_df, routes_df_file)


def prepare_manual_df(manual_csv_file, manual_df_file, verbose=VERBOSE) -> None:
    """Create a dataframe from a csv file with manually classified holds."""
    manual_df = pd.read_csv(manual_csv_file, sep=";", decimal=",")
    manual_df.fillna('', inplace=True)

    # Fix coordinates
    manual_df["x"] = manual_df.apply(lambda x: ord(x.x) - 65, axis=1)
    manual_df["y"] = manual_df.apply(lambda x: x.y - 1, axis=1)

    manual_df = manual_df.set_index(["x", "y"])

    if verbose:
        print(manual_df)

    save_object(manual_df, manual_df_file)


def get_hold_scores(routes_df_file, manual_df_file, hold_scores_file, manual=False, verbose=VERBOSE) -> None:
    """Calculate the scores for each hold.

    The hold score is the average of the normalized grades of the routes that use the hold. For each hold a summary is
    created to support the claim of the hold score. The hold score is also compared to the manual classification.
    """
    routes_df = load_object(routes_df_file)

    if verbose:
        print(routes_df.groupby(["grade"]).size())
        # Make sure all grades higher than 7C+ are in the same bin
        # routes_df["grade"] = routes_df["grade"].apply(
        #     lambda x: x if x not in ["7C+", "8A", "8A+", "8B", "8B+", "8C", "8C+"] else "7C+")
        # print(routes_df.groupby(["Grade"]).size())
        # fig = px.histogram(routes_df, x="Grade", category_orders=dict(Grade=USED_GRADES))
        # fig.show()
        # fig.write_image("../plots/grade_distribution.png", format="png")
        # fig.write_image("../plots/grade_distribution.pdf")
    hold_scores_df = routes_df.explode("moves").reset_index()
    hold_scores_df[["x", "y"]] = pd.DataFrame(hold_scores_df["moves"].to_list())

    # Calculate summary statistics per hold
    hold_scores_df = hold_scores_df.groupby(["x", "y"]).agg(number_of_routes=("normalized_grade", "size"),
                                                            grade_avg=("normalized_grade", "mean"),
                                                            grade_std=("normalized_grade", "std"))

    # Calculate the hold score per hold by scaling the average grade to [0, 1]
    min_hold_score = min(hold_scores_df["grade_avg"])
    max_hold_score = max(hold_scores_df["grade_avg"])
    hold_scores_df["hold_score"] = hold_scores_df.apply(
        lambda x: (x.grade_avg - min_hold_score) / (max_hold_score - min_hold_score), axis=1)

    if manual:
        manual_df = load_object(manual_df_file)
        # Add the manual classification
        hold_scores_df = pd.merge(hold_scores_df, manual_df, on=["x", "y"])

        hold_scores_df["hold_types"] = hold_scores_df[["hold_type_1", "hold_type_2", "hold_type_3"]].values.tolist()
        hold_scores_df["hold_types"] = hold_scores_df.apply(lambda x: [a for a in x.hold_types if a], axis=1)
        hold_scores_df = hold_scores_df.drop(["hold_type_1", "hold_type_2", "hold_type_3"], axis=1)

        # Compare the manual classification to the hold score
        min_manual_difficulty = min(hold_scores_df["manual_difficulty"])
        max_manual_difficulty = max(hold_scores_df["manual_difficulty"])
        hold_scores_df["normalized_manual_difficulty"] = hold_scores_df.apply(
            lambda x: (x.manual_difficulty - min_manual_difficulty) / (max_manual_difficulty - min_manual_difficulty),
            axis=1)
        hold_scores_df["hold_score_manual_difference"] = hold_scores_df["hold_score"] - hold_scores_df[
            "normalized_manual_difficulty"]

        # Add the hold rotations
        hold_scores_df["rotations"] = hold_scores_df.apply(lambda x: rotations_from_text(x.rotations), axis=1)

    if verbose:
        print(hold_scores_df.to_string())

    save_object(hold_scores_df, hold_scores_file)


def get_hold_score(coordinates, year=YEAR, board=BOARD) -> float:
    """Get the hold score for a given coordinate."""
    return load_object(f"../data/hold_scores/{year}_{board}_hold_scores.pkl").loc[tuple(coordinates), "hold_score"]


def get_hold_rotations(coordinates, year=YEAR, board=BOARD) -> list[float]:
    """Get the hold rotations for a given coordinate."""
    return load_object(f"../data/hold_scores/{year}_{board}_hold_scores.pkl").loc[tuple(coordinates), "rotations"]


def show_routes(routes_df, verbose=VERBOSE) -> None:
    """For a routes dataframe, show a summary of the routes."""
    if not verbose:
        return
    print(f"\n\nThere are {len(routes_df)} routes:")
    print(routes_df.groupby(["grade"]).size().to_string())
    print(routes_df.groupby(["route_length"]).size().to_string())
    print(routes_df.groupby(["grade", "route_length"]).size().to_string())


def show_individual_routes(routes_df, verbose=VERBOSE) -> None:
    """For a routes dataframe, show the individual routes."""
    if not verbose:
        return
    print(f"\n\nThere are {len(routes_df)} routes:")
    for index, route in routes_df.iterrows():
        visualise_route(route["moves"], route["grade"])


def show_hold_scores(hold_scores_file, year=YEAR, board=BOARD, manual=False, verbose=VERBOSE) -> None:
    """Visualise the hold scores for a given year and board."""
    with open(hold_scores_file, "rb") as f:
        hold_scores_df = pickle.load(f)
    features = ["hold_score", "grade_std", "number_of_routes"]
    if manual:
        features += ["normalized_manual_difficulty", "hold_score_manual_difference"]
    for feature in features:
        pt = pd.pivot_table(hold_scores_df, values=feature, index=["x"], columns=["y"])
        values = pt.to_numpy()

        fig = px.imshow(values.T, color_continuous_scale="Inferno_r", aspect="equal", title=f"{feature}_heatmap")
        fig['layout']['yaxis']['autorange'] = True
        if verbose:
            fig.show()
        # Write the image to a pdf, so that it can be included in the report. Make sure it is compact.
        # fig.write_image(f"../plots/holds/{year}_{board}_{feature}_heatmap.png", scale=1.0, width=500, height=1000,
        #                 engine="kaleido")
        # fig.write_image(f"../plots/holds/{year}_{board}_{feature}_heatmap.pdf", engine="kaleido")

        fig = px.histogram(hold_scores_df, x=feature, title=f"{feature}_histogram")
        if verbose:
            fig.show()
        # fig.write_image(f"../plots/holds/{year}_{board}_{feature}_histogram.pdf", width=1000, height=1000,
        #                 engine="kaleido")


def main() -> None:
    """Main function."""
    try:
        scrape_file = find_scrape_file(YEAR, BOARD)
    except FileNotFoundError as e:
        print(f"Error: {e}")
        return

    routes_df_file = f"../data/routes/{YEAR}_{BOARD}_routes.pkl"
    manual_csv_file = f"../data/hold_scores/{YEAR}_{BOARD}_manual.csv"
    manual_df_file = f"../data/hold_scores/{YEAR}_{BOARD}_manual.pkl"
    hold_scores_file = f"../data/hold_scores/{YEAR}_{BOARD}_hold_scores.pkl"

    prepare_routes_df(scrape_file, routes_df_file)
    # prepare_manual_df(manual_csv_file, manual_df_file)
    get_hold_scores(routes_df_file, manual_df_file, hold_scores_file)
    show_hold_scores(hold_scores_file, YEAR, BOARD)


if __name__ == "__main__":
    main()
