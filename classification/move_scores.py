import os
import time
from random import random

import plotly.express as px
from sklearn.discriminant_analysis import QuadraticDiscriminantAnalysis, LinearDiscriminantAnalysis
from sklearn.dummy import DummyClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier, AdaBoostClassifier, \
    BaggingClassifier, HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression, SGDClassifier, Perceptron, PassiveAggressiveClassifier, \
    RidgeClassifier
from sklearn.metrics import confusion_matrix
from sklearn.naive_bayes import GaussianNB, BernoulliNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC, LinearSVC
from sklearn.tree import ExtraTreeClassifier, DecisionTreeClassifier

from helpers.files import *
from helpers.grade_conversion import *
from helpers.moonboard import *
from sequencing.move_scoring import score_footholds
from settings import *


def prepare_moves_df(sequenced_routes_df_file: str, moves_df_file: str, verbose: bool = VERBOSE) -> None:
    """Convert the sequenced routes dataframe to a moves dataframe, ready to be used for training."""
    sequenced_routes_df: pd.DataFrame = load_object(sequenced_routes_df_file)

    moves_df = sequenced_routes_df.explode("sequence")[
        ["sequence", "ordinal_grade", "normalized_grade", "font_index", "grade"]]
    moves_df = moves_df.reset_index()

    if verbose:
        print(moves_df.describe())

    split_moves_df = pd.DataFrame(moves_df["sequence"].tolist(),
                                  columns=["holds", "left_hold", "right_hold", "next_hold", "next_hand"])
    moves_df = pd.concat([moves_df, split_moves_df], axis=1)

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

    if verbose:
        print("Calculating foot scores")
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

    moves_df = moves_df[
        ["index", "normalized_grade", "ordinal_grade", "font_index", "grade", "n_s_x", "n_s_y", "n_m_x", "n_m_y",
         "stationary_distance", "moving_distance", "stationary_score", "moving_score", "next_score", "holds_score",
         "foot_score", "r_s_x", "r_s_y", "r_m_x", "r_m_y", "r_n_x", "r_n_y"]]

    ord_moves_df = pd.DataFrame(moves_df["ordinal_grade"].tolist(),
                                columns=[f"ord_{ord_index}" for ord_index in range(len(USED_GRADES) - 1)])
    moves_df = pd.concat([moves_df, ord_moves_df], axis=1)

    if verbose:
        print(moves_df)
    save_object(moves_df, moves_df_file)


def show_moves_df(moves_df_file, year=YEAR, board=BOARD):
    moves_df = load_object(moves_df_file)
    print(moves_df.info())

    moves_df["stationary_x"] = moves_df.apply(lambda x: x.n_s_x - .5 + random(), axis=1)
    moves_df["stationary_y"] = moves_df.apply(lambda x: x.n_s_y - .5 + random(), axis=1)
    fig = px.scatter(moves_df, x="stationary_x", y="stationary_y", color="normalized_grade",
                     color_continuous_scale="Inferno_r")
    fig.update_traces(marker_size=4)
    fig.show()
    # fig.write_image(f"../plots/moves/{year}_{board}_stationary_x_y.png", engine="kaleido", scale=0.01)
    moves_df = moves_df.drop(["stationary_x", "stationary_y"], axis=1)

    moves_df["moving_x"] = moves_df.apply(lambda x: x.n_m_x - .5 + random(), axis=1)
    moves_df["moving_y"] = moves_df.apply(lambda x: x.n_m_y - .5 + random(), axis=1)
    fig = px.scatter(moves_df, x="moving_x", y="moving_y", color="normalized_grade", color_continuous_scale="Inferno_r")
    fig.update_traces(marker_size=4)
    fig.show()
    # fig.write_image(f"../plots/moves/{year}_{board}_moving_x_y.png", engine="kaleido", scale=0.1)
    moves_df = moves_df.drop(["moving_x", "moving_y"], axis=1)

    print(moves_df.info())

    fig = px.scatter_matrix(moves_df, dimensions=["stationary_score", "moving_score", "next_score", "holds_score",
                                                  "stationary_distance", "moving_distance"],
                            color="normalized_grade", color_continuous_scale="Inferno_r")
    fig.show()
    # fig.write_image(f"../plots/moves/{year}_{board}_hold_scores_matrix.png", engine="kaleido")

    fig = px.scatter_3d(moves_df, x="stationary_score", y="moving_score", z="next_score",
                        color="normalized_grade", color_continuous_scale="Inferno_r")
    fig.show()
    # fig.write_image(f"../plots/moves/{year}_{board}_hold_scores.png", engine="kaleido")

    moves_df["r_stationary_x"] = moves_df["r_s_x"] + np.random.normal(0, .15, len(moves_df))
    moves_df["r_stationary_y"] = moves_df["r_s_y"] + np.random.normal(0, .15, len(moves_df))
    fig = px.scatter(moves_df, x="r_stationary_x", y="r_stationary_y", color="normalized_grade",
                     color_continuous_scale="Inferno_r")
    fig.update_traces(marker_size=4)
    fig.show()

    moves_df["r_moving_x"] = moves_df["r_m_x"] + np.random.normal(0, .15, len(moves_df))
    moves_df["r_moving_y"] = moves_df["r_m_y"] + np.random.normal(0, .15, len(moves_df))
    fig = px.scatter(moves_df, x="r_moving_x", y="r_moving_y", color="normalized_grade",
                     color_continuous_scale="Inferno_r")
    fig.update_traces(marker_size=4)
    fig.show()

    moves_df["r_next_x"] = moves_df["r_n_x"] + np.random.normal(0, .15, len(moves_df))
    moves_df["r_next_y"] = moves_df["r_n_y"] + np.random.normal(0, .15, len(moves_df))
    fig = px.scatter(moves_df, x="r_next_x", y="r_next_y", color="normalized_grade", color_continuous_scale="Inferno_r")
    fig.update_traces(marker_size=4)
    fig.show()

    fig = px.scatter_matrix(moves_df,
                            dimensions=["r_stationary_x", "r_stationary_y", "r_moving_x", "r_moving_y", "r_next_x",
                                        "r_next_y"],
                            color="normalized_grade", color_continuous_scale="Inferno_r")
    fig.update_traces(diagonal_visible=False)
    fig.update_traces(marker_size=1)
    fig.show()
    # fig.write_image(f"../plots/moves/{year}_{board}_hold_rotations.png", engine="kaleido")
    moves_df = moves_df.drop(["r_stationary_x", "r_stationary_y", "r_moving_x", "r_moving_y", "r_next_x", "r_next_y"],
                             axis=1)

    moves_df = moves_df.drop(["index", "font_index"],
                             axis=1)
    fig = px.imshow(moves_df.corr(method="pearson").round(3).apply(abs), text_auto=True,
                    color_continuous_scale="Inferno_r")
    fig.show()
    # fig.write_image(f"../plots/moves/{year}_{board}_correlations.png", engine="kaleido")

    fig = px.histogram(moves_df, x="grade", nbins=15, category_orders={"grade": FONT_GRADES})
    fig.show()
    # fig.write_image(f"../plots/moves/{year}_{board}_grade_histogram.png", engine="kaleido")


def fit_ordinal_move_scores(moves_df_file: str, split_moves_df_file: str, year: str = YEAR, board: str = BOARD,
                            verbose: bool = False) -> None:
    """Ask which move scorer should be trained, then train it.

    In order to improve performance, a thread can be started for each scorer.
    """
    ord_index = int(input(f"Which index should be trained? (Min: 0, Max: {len(USED_GRADES) - 2})\n"))

    if ord_index not in list(range(len(USED_GRADES) - 1)):
        print(f"Invalid index: {ord_index}")
        return

    models = {
        "dummy": DummyClassifier(strategy="most_frequent"),
        "hgbrt": HistGradientBoostingClassifier(random_state=0, max_depth=100, learning_rate=0.01, max_iter=100000),
        "gbrt": GradientBoostingClassifier(random_state=0, max_depth=20, learning_rate=0.01, n_estimators=1000),
        "mlp": MLPClassifier(random_state=0, max_iter=10000, hidden_layer_sizes=(100, 100, 100, 100, 100)),
        "ada": AdaBoostClassifier(random_state=0, n_estimators=1000),
        "svc": SVC(random_state=0, max_iter=100000, kernel="rbf", gamma="scale"),
        "lsvc": LinearSVC(random_state=0, max_iter=100000),
        "rf": RandomForestClassifier(random_state=0, n_estimators=1000, max_depth=100),
        "lr": LogisticRegression(random_state=0, max_iter=10000),
        "knn": KNeighborsClassifier(n_neighbors=5),
        "sgd": SGDClassifier(random_state=0, max_iter=10000, loss="modified_huber"),
        "dt": DecisionTreeClassifier(random_state=0, max_depth=100),
        "etree": ExtraTreeClassifier(random_state=0, max_depth=100),
        "gnb": GaussianNB(),
        "bnb": BernoulliNB(),
        "bag": BaggingClassifier(random_state=0, n_estimators=1000, max_samples=0.5, max_features=0.5),
        "qda": QuadraticDiscriminantAnalysis(),
        "lda": LinearDiscriminantAnalysis(),
        "perceptron": Perceptron(random_state=0, max_iter=10000),
        "passive_aggressive": PassiveAggressiveClassifier(random_state=0, max_iter=10000),
        "ridge": RidgeClassifier(random_state=0, max_iter=10000),
    }

    # Check if the split moves df exists
    if not os.path.exists(split_moves_df_file):
        moves_df = load_object(moves_df_file)
        print(moves_df.info())

        moves_df["center_distance"] = moves_df.apply(
            lambda x: np.sqrt((x.n_s_x - x.n_m_x) ** 2 + (x.n_s_y - x.n_m_y) ** 2),
            axis=1)

        # Set a seed for reproducibility
        np.random.seed(0)

        # Create a dataframe of the unique indices in moves_df
        unique_indices_df = moves_df[["index"]].drop_duplicates()
        # Add a column to unique_indices_df that indicates whether the index is used in the training set. Use a random
        # 75% of the indices.
        unique_indices_df["train"] = np.random.choice([True, False], len(unique_indices_df), p=[0.75, 0.25])
        # Merge the unique_indices_df with moves_df
        moves_df = moves_df.merge(unique_indices_df, on="index", how="left")

        print(moves_df)
        print(moves_df.head(300))

        # Save the whole moves_df to a file
        save_object(moves_df, split_moves_df_file)
    else:
        moves_df = load_object(split_moves_df_file)

    X_train = moves_df[moves_df["train"]][
        ["stationary_score", "moving_score", "next_score", "holds_score", "n_s_x", "n_s_y", "n_m_x", "n_m_y",
         "stationary_distance", "moving_distance", "center_distance", "foot_score", "r_m_x", "r_m_y", "r_n_x",
         "r_n_y", "r_s_x", "r_s_y"]]
    y_train = moves_df[moves_df["train"]][f"ord_{ord_index}"]

    X_test = moves_df[~moves_df["train"]][
        ["stationary_score", "moving_score", "next_score", "holds_score", "n_s_x", "n_s_y", "n_m_x", "n_m_y",
         "stationary_distance", "moving_distance", "center_distance", "foot_score", "r_m_x", "r_m_y", "r_n_x",
         "r_n_y", "r_s_x", "r_s_y"]]
    y_test = moves_df[~moves_df["train"]][f"ord_{ord_index}"]

    for model_name, model in models.items():
        # Skip models that are already trained
        if os.path.exists(f"../data/models/moves/{year}_{board}_{model_name}_{ord_index}.pkl"):
            continue

        if verbose:
            print(f"Training {model_name}...")

        # Time the training
        start = time.thread_time()
        model.fit(X_train, y_train)
        run_time = time.thread_time() - start

        if verbose:
            print(f"Training {model_name} took {run_time:.2f} seconds.")

        # Create a confusion matrix
        y_pred = model.predict(X_test)
        tn, fp, fn, tp = confusion_matrix(y_test, y_pred).ravel()

        if verbose:
            print(f"Score: {model.score(X_test, y_test)}")
            print(f"Confusion matrix:\n{confusion_matrix(y_test, model.predict(X_test))}")

        save_object(model, f"../data/models/moves/{year}_{board}_{model_name}_{ord_index}.pkl")

        # Append the model performance to the performance file
        with open(f"../data/models/moves/{year}_{board}_performance.csv", "a") as f:
            f.write(f"{model_name},{ord_index},{model.score(X_test, y_test)},{tn},{fp},{fn},{tp},{run_time:.2f}\n")

    if verbose:
        print("Done.")


def show_performance(year: str = YEAR, board: str = BOARD, verbose: bool = VERBOSE) -> None:
    # Load the performance file, use the first line as the column names
    performance_df = pd.read_csv(f"../data/models/moves/{year}_{board}_performance.csv", header=0)

    # Create a new dataframe with the model names as index and the ord_index as columns. Use the score as values.
    performance_df = performance_df.pivot(index="model", columns="ord_index", values="score")

    # Sort the models by their average score
    performance_df["average"] = performance_df.mean(axis=1)
    performance_df.sort_values("average", ascending=False, inplace=True)
    performance_df.drop("average", axis=1, inplace=True)

    if verbose:
        print(performance_df)


def main() -> None:
    """Main function."""
    sequenced_routes_df_file = f"../data/routes/{YEAR}_{BOARD}_sequenced_routes.pkl"
    moves_df_file = f"../data/move_scores/{YEAR}_{BOARD}_moves.pkl"
    split_moves_df_file = f"../data/move_scores/{YEAR}_{BOARD}_split_moves.pkl"

    # prepare_moves_df(sequenced_routes_df_file, moves_df_file)
    # show_moves_df(moves_df_file)
    # fit_move_scores(moves_df_file, verbose=True)

    # fit_ordinal_move_scores(moves_df_file, split_moves_df_file, verbose=True)
    show_performance()


if __name__ == "__main__":
    main()
