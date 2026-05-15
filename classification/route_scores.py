import os
from typing import Callable

import numpy as np
from sklearn.dummy import DummyClassifier
from sklearn.neural_network import MLPClassifier

from helpers.files import *
from helpers.grade_conversion import *
from helpers.moonboard import get_move_vectors, get_vector_distance
from sequencing.move_scoring import score_footholds
from sequencing.search import beam_search
from settings import *


def take_top(x, top: int, skip_top: int) -> str:
    if top == -1:
        top = len(x) - 1
    top = min(top + skip_top, len(x) - 1)
    if skip_top >= top:
        skip_top = top - 1
    return x[skip_top:top]


def combine_moves_vertical(moves: list[list[float]], grader: Callable = ordinal_probabilities_to_font, top: int = -1,
                           skip_top: int = 0) -> str:
    # Sort the moves by the average probability
    moves.sort(key=lambda x: sum(x) / len(x), reverse=True)
    # Take the top max moves, skipping the top skip_top moves
    moves = take_top(moves, top, skip_top)

    probabilities = [0 for _ in range(len(USED_GRADES) - 1)]
    for move in moves:
        probabilities = [probabilities[index] + move[index] for index in range(len(USED_GRADES) - 1)]

    probabilities = [probabilities[index] / len(moves) for index in range(len(USED_GRADES) - 1)]
    return grader(probabilities)


def combine_moves_horizontal(moves: list[list[float]], grader: Callable = ordinal_probabilities_to_font, top: int = -1,
                             skip_top: int = 0) -> str:
    # Calculate the grade for each move in moves
    results = [font_to_index(grader(move)) for move in moves]
    # Sort the moves so the most difficult moves are at the top
    results.sort(reverse=True)
    # Take the top max moves, skipping the top skip_top moves
    results = take_top(results, top, skip_top)
    # Return the average of the remaining moves, using the closest integer when converting the index to a grade
    return index_to_font(round(sum(results) / len(results)))


def train_ord_to_font(move_model_name, grouped_moves_df, year: str = YEAR, board: str = BOARD) -> None:
    models = {
        "dummy": DummyClassifier(strategy="most_frequent"),
        # "hgbrt": HistGradientBoostingClassifier(random_state=0, max_depth=100, learning_rate=0.01, max_iter=100000),
        "mlp": MLPClassifier(random_state=0, max_iter=10000, hidden_layer_sizes=(100, 100, 100, 100, 100)),
        # "ada": AdaBoostClassifier(random_state=0, n_estimators=1000),
        # "rf": RandomForestClassifier(random_state=0, n_estimators=1000, max_depth=100),
    }

    # Explode the moves into a list of moves
    grouped_moves_df = grouped_moves_df.explode(f"{move_model_name}_probs")
    grouped_moves_df["one_hot_grade"] = grouped_moves_df.apply(
        lambda x: font_to_one_hot(x.grade), axis=1)

    # Split the data into training and testing sets based on the train column
    train_df = grouped_moves_df[grouped_moves_df["train"]]
    test_df = grouped_moves_df[~grouped_moves_df["train"]]

    for model_name, model in models.items():
        # Check if the model has already been trained
        if os.path.isfile(f"../data/models/ord_to_font/{year}_{board}_{move_model_name}_{model_name}.pkl"):
            continue
        print(f"Training {move_model_name} - {model_name}")

        # Train the model
        model.fit(train_df[f"{move_model_name}_probs"].tolist(), train_df["one_hot_grade"].tolist())
        # Save the model to a file
        save_object(model, f"../data/models/ord_to_font/{year}_{board}_{move_model_name}_{model_name}.pkl")

        # Append the model performance to the performance file
        with open(f"../data/models/ord_to_font/{year}_{board}_performance.csv", "a") as f:
            f.write(
                f"{move_model_name},{model_name},{model.score(test_df[f'{move_model_name}_probs'].tolist(), test_df['one_hot_grade'].tolist())}\n")


class MoveCombiner:
    def __init__(self, combiner: str = "vertical", grader: Callable = ordinal_probabilities_to_font, top: int = -1,
                 skip_top: int = 0):
        self.combiner = combiner
        self.grader = grader
        self.top = top
        self.skip_top = skip_top

    def __str__(self):
        return f"{self.combiner}_{self.grader.__name__}_{self.top}_{self.skip_top}"

    def combine_moves(self, moves: list[list[float]]) -> str:
        if self.combiner == "vertical":
            return combine_moves_vertical(moves, self.grader, self.top, self.skip_top)
        if self.combiner == "horizontal":
            return combine_moves_horizontal(moves, self.grader, self.top, self.skip_top)


def predict_route_grades(split_moves_df_file: str, year: str = YEAR, board: str = BOARD,
                         verbose: bool = VERBOSE) -> None:
    # models = ["dummy", "hgbrt", "gbrt", "mlp", "ada", "svc", "lsvc", "rf", "lr", "knn", "sgd", "dt", "etree", "gnb",
    #           "bnb", "bag", "qda", "lda", "perceptron", "passive_aggressive", "ridge"]
    # Remove svc, lsvc, perceptron, passive_aggresive and ridge as they have not been trained with probabilities
    models = ["dummy", "hgbrt", "gbrt", "mlp", "ada", "rf", "lr", "knn", "sgd", "dt", "etree", "gnb", "bnb",
              "bag", "qda", "lda"]

    # Load the route data
    moves_df = load_object(split_moves_df_file)

    for model_name in models:
        print(model_name)
        for ord_index in range(len(USED_GRADES) - 1):
            model_file = f"../data/models/moves/{year}_{board}_{model_name}_{ord_index}.pkl"

            if not os.path.exists(model_file):
                continue

            model = load_object(model_file)
            probabilities = model.predict_proba(
                moves_df[["stationary_score", "moving_score", "next_score", "holds_score", "n_s_x", "n_s_y", "n_m_x",
                          "n_m_y", "stationary_distance", "moving_distance", "center_distance", "foot_score", "r_m_x",
                          "r_m_y", "r_n_x", "r_n_y", "r_s_x", "r_s_y"]])
            moves_df[f"{model_name}_{ord_index}"] = probabilities[:, 1]

        # Combine the probabilities into a list
        moves_df[f"{model_name}_probs"] = moves_df.apply(
            lambda x: [x[f"{model_name}_{index}"] for index in range(len(USED_GRADES) - 1)], axis=1)

        # Drop the individual probabilities
        moves_df.drop([f"{model_name}_{index}" for index in range(len(USED_GRADES) - 1)], axis=1, inplace=True)

    # Group the moves by route, appending the probabilities of each model into a list and keeping the grade
    aggregates = {
        "grade": "first",
        "train": "first",
    }
    for model in models:
        aggregates[f"{model}_probs"] = lambda x: list(x)
    grouped_moves_df = moves_df.groupby("index").agg(aggregates)
    grouped_moves_df.reset_index(inplace=True)
    grouped_moves_df.drop("index", axis=1, inplace=True)

    # Change any grade higher than 7C+ to 7C+
    grouped_moves_df["grade"] = grouped_moves_df.apply(
        lambda x: "7C+" if font_to_index(x.grade) > font_to_index("7C+") else x.grade, axis=1)

    # for model in models:
    #     train_ord_to_font(model, grouped_moves_df)

    graders = [ordinal_probabilities_to_font]
    move_combiners = []
    for top in list(range(1, 6)) + [-1]:
        for skip_top in range(0, 5):
            for grader in graders:
                for combiner in ["vertical", "horizontal"]:
                    move_combiners.append(MoveCombiner(combiner, grader, top, skip_top))

    for model in models:
        for move_combiner in move_combiners:
            if verbose:
                print(f"Predicting {model} - {move_combiner}")

            # Combine the probabilities of the top moves with the skip_top highest probabilities removed
            grouped_moves_df[f"{model}_{move_combiner}"] = grouped_moves_df.apply(
                lambda x: move_combiner.combine_moves(x[f"{model}_probs"]), axis=1)

            # Calculate the accuracy of the grade predictions
            grouped_moves_df[f"{model}_{move_combiner}_accuracy"] = grouped_moves_df.apply(
                lambda x: 1 if x[f"{model}_{move_combiner}"] == x["grade"] else 0, axis=1)
            accuracy = grouped_moves_df[f"{model}_{move_combiner}_accuracy"].sum() / len(
                grouped_moves_df)

            # Calculate the one-off accuracy of the grade predictions
            grouped_moves_df[f"{model}_{move_combiner}_one_off_accuracy"] = grouped_moves_df.apply(
                lambda x: 1 if font_n_off(x[f"{model}_{move_combiner}"], x["grade"], 1) else 0, axis=1)
            one_off_accuracy = grouped_moves_df[f"{model}_{move_combiner}_one_off_accuracy"].sum() / len(
                grouped_moves_df)

            # Calculate the two-off accuracy of the grade predictions
            grouped_moves_df[f"{model}_{move_combiner}_two_off_accuracy"] = grouped_moves_df.apply(
                lambda x: 1 if font_n_off(x[f"{model}_{move_combiner}"], x["grade"], 2) else 0, axis=1)
            two_off_accuracy = grouped_moves_df[f"{model}_{move_combiner}_two_off_accuracy"].sum() / len(
                grouped_moves_df)

            # Calculate the three-off accuracy of the grade predictions
            grouped_moves_df[f"{model}_{move_combiner}_three_off_accuracy"] = grouped_moves_df.apply(
                lambda x: 1 if font_n_off(x[f"{model}_{move_combiner}"], x["grade"], 3) else 0, axis=1)
            three_off_accuracy = grouped_moves_df[f"{model}_{move_combiner}_three_off_accuracy"].sum() / len(
                grouped_moves_df)

            # Calculate the four-off accuracy of the grade predictions
            grouped_moves_df[f"{model}_{move_combiner}_four_off_accuracy"] = grouped_moves_df.apply(
                lambda x: 1 if font_n_off(x[f"{model}_{move_combiner}"], x["grade"], 4) else 0, axis=1)
            four_off_accuracy = grouped_moves_df[f"{model}_{move_combiner}_four_off_accuracy"].sum() / len(
                grouped_moves_df)

            # Calculate the five-off accuracy of the grade predictions
            grouped_moves_df[f"{model}_{move_combiner}_five_off_accuracy"] = grouped_moves_df.apply(
                lambda x: 1 if font_n_off(x[f"{model}_{move_combiner}"], x["grade"], 5) else 0, axis=1)
            five_off_accuracy = grouped_moves_df[f"{model}_{move_combiner}_five_off_accuracy"].sum() / len(
                grouped_moves_df)
            # Append the accuracy and one-off accuracy to the performance file
            # Append the model performance to the performance file
            with open(f"../data/models/routes/{year}_{board}_performance.csv", "a") as f:
                f.write(
                    f"{model},{move_combiner},{accuracy},{one_off_accuracy},{two_off_accuracy},{three_off_accuracy},{four_off_accuracy},{five_off_accuracy}\n")


def predict_route_grade(sequence, model_name: str = "rf", year: str = YEAR, board: str = BOARD,
                        verbose: bool = VERBOSE) -> str:
    """Predicts the grade of a route given the holds and the year and board of the route."""
    # print(f"sequence: {sequence.holds}")
    # x = beam_search(sequence.holds, 0, 3, 5)
    # print(f"sequence.sequence: {sequence.sequence}")
    # print(f"x: {x}")
    moves_df = pd.DataFrame(beam_search(sequence.holds, 0, 3, 5)[0],
                            columns=["holds", "left_hold", "right_hold", "next_hold", "next_hand"])

    # Create possible features as new columns
    moves_df["stationary_hold"] = moves_df.apply(lambda x: x.left_hold if x.next_hand == "r" else x.right_hold, axis=1)
    moves_df["moving_hold"] = moves_df.apply(lambda x: x.left_hold if x.next_hand == "l" else x.right_hold, axis=1)
    moves_df[["n_s_x", "n_s_y", "n_m_x", "n_m_y"]] = moves_df.apply(
        lambda x: get_move_vectors(x.stationary_hold, x.moving_hold, x.next_hold), axis=1, result_type="expand")

    moves_df["stationary_distance"] = moves_df.apply(lambda x: get_vector_distance(x.n_s_x, x.n_s_y), axis=1)
    moves_df["moving_distance"] = moves_df.apply(lambda x: get_vector_distance(x.n_m_x, x.n_m_y), axis=1)

    # Directly look up the score of holds to increase performance
    hold_scores = load_object(f"../data/hold_scores/2017_moonboard_hold_scores.pkl")
    moves_df["stationary_score"] = moves_df.apply(lambda x: hold_scores.loc[tuple(x.stationary_hold), "hold_score"],
                                                  axis=1)
    moves_df["moving_score"] = moves_df.apply(lambda x: hold_scores.loc[tuple(x.moving_hold), "hold_score"], axis=1)
    moves_df["next_score"] = moves_df.apply(lambda x: hold_scores.loc[tuple(x.next_hold), "hold_score"], axis=1)
    moves_df["holds_score"] = moves_df.apply(
        lambda x: np.sqrt(np.power(x.stationary_score, 2) + np.power(x.moving_score, 2) + np.power(x.next_score, 2)),
        axis=1)

    moves_df["stationary_rotations"] = moves_df.apply(lambda x: hold_scores.loc[tuple(x.stationary_hold), "rotations"],
                                                      axis=1)
    moves_df["moving_rotations"] = moves_df.apply(lambda x: hold_scores.loc[tuple(x.moving_hold), "rotations"], axis=1)
    moves_df["next_rotations"] = moves_df.apply(lambda x: hold_scores.loc[tuple(x.next_hold), "rotations"], axis=1)

    moves_df["foot_score"] = moves_df.apply(lambda x: score_footholds(x.holds, x.left_hold, x.right_hold, x.next_hold),
                                            axis=1)

    moves_df[["r_s_x", "r_s_y"]] = moves_df.apply(
        lambda x: [x.stationary_rotations[0][0], x.stationary_rotations[0][1]] if x.next_hand == "r" else [
            -1. * x.stationary_rotations[0][0], x.stationary_rotations[0][1]], axis=1, result_type="expand")
    moves_df[["r_m_x", "r_m_y"]] = moves_df.apply(
        lambda x: [x.moving_rotations[0][0], x.moving_rotations[0][1]] if x.next_hand == "r" else [
            -1. * x.moving_rotations[0][0], x.moving_rotations[0][1]], axis=1, result_type="expand")
    moves_df[["r_n_x", "r_n_y"]] = moves_df.apply(
        lambda x: [x.next_rotations[0][0], x.next_rotations[0][1]] if x.next_hand == "r" else [
            -1. * x.next_rotations[0][0], x.next_rotations[0][1]], axis=1, result_type="expand")

    moves_df["center_distance"] = moves_df.apply(
        lambda x: np.sqrt((x.n_s_x - x.n_m_x) ** 2 + (x.n_s_y - x.n_m_y) ** 2), axis=1)

    moves_df = moves_df[
        ["stationary_score", "moving_score", "next_score", "holds_score", "n_s_x", "n_s_y", "n_m_x", "n_m_y",
         "stationary_distance", "moving_distance", "center_distance", "foot_score", "r_m_x", "r_m_y", "r_n_x",
         "r_n_y", "r_s_x", "r_s_y"]]

    predict_moves_df = moves_df.copy()

    for ord_index in range(len(USED_GRADES) - 1):
        model = load_object(f"../data/models/moves/{year}_{board}_{model_name}_{ord_index}.pkl")
        predict_moves_df[f"grade_{ord_index}"] = model.predict_proba(moves_df)[:, 1]

    moves_df["probabilities"] = predict_moves_df.apply(
        lambda x: [x[f"grade_{ord_index}"] for ord_index in range(len(USED_GRADES) - 1)], axis=1)
    # Get the column probabilities as a python list
    probabilities = moves_df["probabilities"].tolist()
    move_combiner = MoveCombiner("vertical", ordinal_probabilities_to_font, -1, 0)
    grade = move_combiner.combine_moves(probabilities)
    return grade


def main() -> None:
    split_moves_df_file = f"../data/move_scores/{YEAR}_{BOARD}_split_moves.pkl"

    predict_route_grades(split_moves_df_file)
    # Test the combine_moves function with a list of 5 sublists of 10 probabilities each
    # print(combine_moves([[0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.1],
    #                      [0.1, 0.2, 0.4, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.2],
    #                      [0.1, 0.2, 0.2, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.55],
    #                      [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.143],
    #                      [0.1, 0.2, 0.5, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 0.143]], 2, 1))


if __name__ == "__main__":
    main()
