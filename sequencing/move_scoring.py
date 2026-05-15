"""Move scoring used in sequencing of routes."""

import os

import matplotlib.pyplot as plt
import seaborn as sns
from PyNomaly import loop
from PyNomaly.loop import LocalOutlierProbability
from scipy.stats import norm

from classification.hold_scores import get_hold_rotations
from helpers.files import *
from helpers.moonboard import *
from helpers.moonboard_tui import *
from settings import *


def score_distance(left, right, next, reach=10.) -> float:
    """Calculates a score based on the distance of the next hold.

    The score is 0.0 if the next hold is at the easiest distance. The score is 1.0 if the next hold is too far away. The
    function is symmetric, so left and right are interchangeable. As we are only interested in the easiest move, we can
    ignore the optimal distance for the next hold, and just look for the """
    center = coordinate_center(left, right)
    distance = get_coordinate_distance(center, next)
    # Normalize the distance to receive a score of 1 for the optimal distance.
    distance_score = 1. - norm.pdf(distance, reach * .1, np.sqrt(reach * 0.5)) / norm.pdf(reach * .1, reach * .1,
                                                                                          np.sqrt(reach * 0.5))
    if distance > reach:
        distance_score = 1.
    if next[1] < center[1]:
        distance_score *= 2.
    if distance_score > 1.:
        distance_score = 1.
    return distance_score


def score_fingers(left_score, right_score, next_score) -> float:
    """Calculates a score based on the difficulty of the holds in the move."""
    return np.mean([left_score, right_score, next_score])


def score_foothold(foothold, center, foot_reach) -> float:
    """Calculate a score for a single foothold.

    Assume the "best" foothold position is at around 2/3 of the reach. The score is 0.0 at this position. In this
    position it is easiest to create momentum for the next move.
    """
    optimal_reach = foot_reach * .66
    distance = get_coordinate_distance(foothold, center)
    distance_score = 1. - norm.pdf(distance, optimal_reach, np.sqrt(foot_reach - optimal_reach))

    if foothold[1] < 0:
        foothold_score = 0.5
    else:
        foothold_score = get_hold_score(foothold)

    # Scale up the hold score. No foothold is worth 1.0, as even the worst foothold is worth 0.5.
    foothold_score = foothold_score / 2.

    # The foothold score is the product of the distance score and the hold score
    return distance_score * foothold_score


def score_footholds(holds, left, right, next_hold, foot_reach=10.) -> float:
    """Calculates a score based on the availability of footholds in the next move."""

    # If holds has type np.ndarray, convert it to a list.
    if type(holds) == np.ndarray:
        holds = holds.tolist()

    # Add the footholds on the kickboard
    footholds = holds + [[x, y] for x in range(0, 11) for y in range(-1, -3, -1)]

    # Remove the footholds that are currently used
    footholds = [foothold for foothold in footholds if foothold != left and foothold != right and foothold != next_hold]

    # Remove the footholds that are above the climbers hands
    footholds = [foothold for foothold in footholds if foothold[1] < max(left[1], right[1])]

    # Remove holds that are too far away
    center = coordinate_center(left, right)
    footholds = [foothold for foothold in footholds if get_coordinate_distance(foothold, center) <= foot_reach]

    # Calculate the foothold score for each foothold. Add a score of 0.0 twice to simulate feet hanging in the air.
    foothold_scores = [1., 1.] + [score_foothold(foothold, center, foot_reach) for foothold in footholds]

    # Return the average of the two best foothold scores
    return np.mean(sorted(foothold_scores)[:2])


def get_move_rotations(left, right, next_hold, next_hand) -> list:
    """Return a list of rotations for a move."""
    left_rotations = get_hold_rotations(left)
    right_rotations = get_hold_rotations(right)
    next_rotations = get_hold_rotations(next_hold)
    if next_hand == "l":
        left_rotations, right_rotations = right_rotations, left_rotations
    return left_rotations + right_rotations + next_rotations


def combine_sequences(sequence_folder, moves_file, verbose=VERBOSE) -> None:
    """Add all manually sequenced routes to a single dataframe to be used for training."""
    moves_df = pd.DataFrame()

    for subdir, dirs, files in os.walk(sequence_folder):
        for file in files:
            if not os.path.splitext(file)[-1].lower() == ".pkl":
                continue
            sequence = pd.DataFrame(load_object(os.path.join(subdir, file)))

            sequence["holds"] = [
                np.unique(list(sequence["left"]) + list(sequence["right"]) + list(sequence["next"]), axis=0) for _ in
                range(len(sequence))]

            moves_df = pd.concat([moves_df, sequence])

    moves_df["center"] = moves_df.apply(lambda x: coordinate_center(x.left, x.right), axis=1)
    moves_df["right_from_right"] = moves_df.apply(
        lambda x: coordinate_next_hold(x.left, x.right, x.next, x.next_hand, True), axis=1)
    moves_df["right_from_left"] = moves_df.apply(
        lambda x: coordinate_next_hold(x.left, x.right, x.next, x.next_hand, False), axis=1)
    # r(ight)_r(ight)_x/y
    moves_df["r_r_x"] = moves_df.apply(lambda x: x.right_from_right[0], axis=1)
    moves_df["r_r_y"] = moves_df.apply(lambda x: x.right_from_right[1], axis=1)
    moves_df["r_l_x"] = moves_df.apply(lambda x: x.right_from_left[0], axis=1)
    moves_df["r_l_y"] = moves_df.apply(lambda x: x.right_from_left[1], axis=1)

    # Add hold scores
    moves_df["moving_score"] = moves_df.apply(lambda x: x.right_score if x.next_hand == "r" else x.left_score, axis=1)
    moves_df["stationary_score"] = moves_df.apply(lambda x: x.left_score if x.next_hand == "r" else x.right_score,
                                                  axis=1)

    # Add a score based on the length of the move
    moves_df["distance_score"] = moves_df.apply(
        lambda x: score_distance(x.left, x.right, x.next), axis=1)

    # Add a combined score for the hold scores
    moves_df["finger_score"] = moves_df.apply(lambda x: score_fingers(x.moving_score, x.stationary_score, x.next_score),
                                              axis=1)

    # Add foothold score
    moves_df["foothold_score"] = moves_df.apply(lambda x: score_footholds(x.holds, x.left, x.right, x.next), axis=1)

    if verbose:
        print(moves_df)

    save_object(moves_df, moves_file)


def train_move_scorer(moves_file, move_scorer_file) -> None:
    """Train a move scorer using the given moves dataframe."""
    moves_df: pd.DataFrame = load_object(moves_file)
    moves_df = moves_df[["r_r_x", "r_r_y", "r_l_x", "r_l_y"]]
    model = loop.LocalOutlierProbability(moves_df, extent=3, n_neighbors=10, progress_bar=True).fit()
    save_object(model, move_scorer_file)


def score_move(holds, left, right, next_hold, next_hand,
               move_scorer_file="../data/sequencer/2017_moonboard_move_scorer.pkl", year=YEAR, board=BOARD,
               verbose=VERBOSE) -> [float]:
    """Score a move based on the given holds, left hand, right hand, next hold and next hand."""
    model: LocalOutlierProbability = load_object(move_scorer_file)

    moving_score = get_hold_score(right, year, board)
    stationary_score = get_hold_score(left, year, board)
    next_score = get_hold_score(next_hold, year, board)

    r_r_y = next_hold[1] - right[1]
    r_l_y = next_hold[1] - left[1]
    if next_hand == "l":
        moving_score, stationary_score = stationary_score, moving_score
        r_r_x = right[0] - next_hold[0]
        r_l_x = left[0] - next_hold[0]
    else:
        r_r_x = next_hold[0] - right[0]
        r_l_x = next_hold[0] - left[0]

    distance_weight = 0.3
    distance_score = score_distance(left, right, next_hold)

    # Check if the move is reachable, if it's not, return 0.
    if distance_score <= 0.:
        return [1.]

    finger_weight = 0.3
    finger_score = score_fingers(moving_score, stationary_score, next_score)
    flow_weight = 0.2
    flow_score = model.stream(np.array([r_r_x, r_r_y, r_l_x, r_l_y]))
    foothold_weight = 0.2
    foothold_score = score_footholds(holds, left, right, next_hold)

    if verbose:
        # print(f"distance: {distance_score}, fingers: {finger_score}, flow: {flow_score}, footholds: {foothold_score}")
        pass

    return [distance_weight * distance_score + finger_weight * finger_score + flow_weight * flow_score +
            foothold_weight * foothold_score]


def plot_moves(moves_file) -> None:
    moves_df: pd.DataFrame = load_object(moves_file)

    moves_df["Moving hand"] = moves_df["right_from_right"]
    moves_df["Stationary hand"] = moves_df["right_from_left"]
    moves_df = moves_df.melt(value_vars=["Stationary hand", "Moving hand"])
    moves_df["With respect to"] = moves_df["variable"]
    moves_df["x"] = moves_df.apply(lambda x: x.value[0], axis=1)
    moves_df["y"] = moves_df.apply(lambda x: x.value[1], axis=1)

    print(moves_df)

    sns.set_style("darkgrid")
    p = sns.jointplot(data=moves_df, x="x", y="y", hue="With respect to", kind="kde", xlim=[-6.5, 6.5], ylim=[-2.5, 10])
    p.fig.suptitle("Vectors of Right Hand Moving")
    p.ax_joint.set_axis_on()
    p.fig.tight_layout()
    p.fig.subplots_adjust(top=0.95)
    p.ax_joint.scatter(0, 0, color="tab:red", linewidth=10)
    plt.savefig("../plots/moving_right_hand.pdf")
    plt.savefig("../plots/moving_right_hand.png", dpi=3600)
    plt.show()


def main():
    sequence_folder = "../data/sequences/"
    moves_file = f"../data/sequencer/{YEAR}_{BOARD}_moves.pkl"
    move_scorer_file = f"../data/sequencer/{YEAR}_{BOARD}_move_scorer.pkl"
    combine_sequences(sequence_folder, moves_file)
    plot_moves(moves_file)
    # train_move_scorer(moves_file, move_scorer_file)

    print(score_move([], [3, 9], [7, 9], [6, 12], "r", move_scorer_file))
    print(score_move([], [3, 9], [7, 9], [7, 10], "r", move_scorer_file))
    print(score_move([], [3, 9], [7, 9], [6, 12], "l", move_scorer_file))
    print(score_move([], [2, 6], [4, 7], [10, 17], "l", move_scorer_file))
    # print(get_move_rotations([0, 0], [1, 1], [2, 2], "l"))


if __name__ == "__main__":
    main()
