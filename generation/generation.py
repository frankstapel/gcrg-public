"""Generation of new routes based on action capabilities."""
import numpy as np
from scipy.stats import norm

from classification.hold_scores import get_hold_score
from classification.route_scores import predict_route_grade
from helpers.grade_conversion import font_to_ircra, font_n_off
from helpers.moonboard import get_all_holds, get_coordinate_distance, coordinate_center, coordinate_number_to_letter
from helpers.moonboard_gui import visualise_route
from sequencing.move_scoring import score_foothold
from sequencing.sequence import Sequence
from settings import *


def ask_action_capabilities() -> tuple:
    reach = float(input("Enter your reach (in holds): "))
    power = float(input("Enter your power (in body weight ratio): "))
    finger_strength = float(input("Enter your finger strength (in body weight ratio): "))
    grade = input("Enter your desired grade: ")
    return reach, power, finger_strength, grade


def generation_grade(grade):
    """Get the grade for the generation algorithm. 0 equals about 6A+, 0.5 equals about 7A/7A+, 1 equals about 7C+."""
    return (font_to_ircra(grade) - 16.5) / 9.


def get_action_capabilities(reach=10., power=1.2, finger_strength=1.2, core_strength=3, grade="6C+",
                            weights=None, ask=False) -> dict:
    """Get the action capabilities of the user."""
    if weights is None:
        weights = {"power": 0.6, "finger_strength": 0.3, "footholds": 0.1}
    if ask:
        reach, power, finger_strength, grade = ask_action_capabilities()

    return {
        "reach": reach,
        # Assumed that power lies roughly between 1.0 and 2.2, convert this to a range between 0 and 1
        "power": (power - 1.) / 1.2,
        # Assumed that finger strength lies roughly between 1.0 and 2.2, convert this to a range between 0 and 1
        "finger_strength": (finger_strength - 1.) / 1.2,
        # Assumed that core strength is a score between 0 and 10, convert this to a range between 0 and 1
        "core_strength": core_strength / 10.,
        "font_grade": grade,
        "grade": generation_grade(grade),
        "weights": weights
    }


def get_start_holds(holds, action_capabilities):
    """Get the start holds based on the action capabilities."""
    # Only look in the first 6 rows and look for holds that match the required finger strengh
    finger_strength = action_capabilities["finger_strength"] * 0.5 + action_capabilities["grade"] * 0.5
    start_holds = [(hold, abs(get_hold_score(hold) - finger_strength)) for hold in holds if hold[1] < 6]
    # Sort the holds based on their score
    start_holds.sort(key=lambda x: x[1])
    # print(start_holds)
    start_holds = [hold[0] for hold in start_holds]
    return start_holds[:8]
    # Return a list of holds with the score closest to the finger strength


def get_reach_cost(left, right, next, next_hand, reach, power, grade) -> float:
    """Calculates a cost based on the reachability of the next hold."""
    center = coordinate_center(left, right)
    moving_distance = get_coordinate_distance(left, next)
    stationary_distance = get_coordinate_distance(right, next)
    if next_hand == "r":
        moving_distance, stationary_distance = stationary_distance, moving_distance
    # center_distance = get_coordinate_distance(center, next)

    # Adjust the reach for the power and grade
    optimal_reach = 1. + reach * .3 + grade * 2. + power * 4.
    # If next hold is the top hold and if it is reachable, it is a good move
    # if next[1] == 17 and moving_distance <= optimal_reach:
    #     return 0.

    # Normalize the distance to receive a cost of 0 for the optimal distance.
    reach_cost = 1. - norm.pdf(moving_distance, optimal_reach, 2.) / \
                 norm.pdf(optimal_reach, optimal_reach, 2.)
    if next[1] == 17 and moving_distance <= optimal_reach:
        return reach_cost * .9
    # Check if the next hold is reachable
    if stationary_distance > reach:
        # print("2")
        return 1.
    if moving_distance > reach:
        # print("3")
        return 1.
    # Check if the next hold is far enough from the current position
    if moving_distance < 2.:
        # print("3")
        return 1.
    if stationary_distance < 2.:
        # print("4")
        return 1.
    # Check if the move is not downwards
    if next[1] <= center[1]:
        # print("5")
        return 1.
    if next[1] <= left[1]:
        # print("6")
        return 1.
    if next[1] <= right[1]:
        # print("7")
        return 1.
    return reach_cost


def get_finger_cost(next_hold, finger_strength, grade) -> float:
    """Calculates a cost based on the difficulty of the holds in the move."""
    next_score = get_hold_score(next_hold)
    # Adjust the finger strength for the grade
    finger_strength = finger_strength * 0.5 + grade * 0.5
    # print(f"finger_strength: {finger_strength}")
    # Normalize the score to receive a cost of 0 for the optimal score.
    return 1. - norm.pdf(next_score, finger_strength, 0.3) / \
        norm.pdf(finger_strength, finger_strength, 0.3)


def get_footholds_cost(holds, left, right, next_hold, core_strength, grade, reach) -> float:
    """Calculates a cost based on the availability of footholds in the next move."""
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
    footholds = [foothold for foothold in footholds if get_coordinate_distance(foothold, center) <= reach]

    # Calculate the foothold score for each foothold. Add a score of 1. twice to simulate feet hanging in the air.
    foothold_scores = [1., 1.] + [score_foothold(foothold, center, reach) for foothold in footholds]

    # Get the best two footholds
    foothold_scores = sorted(foothold_scores)[:2]

    # Calculate the optimal foothold score.
    optimal_foothold_score = core_strength * 0.75 + grade * 0.25

    # Return the average difference between the best foothold scores and the optimal foothold score.
    return np.mean([abs(foothold_scores[0] - optimal_foothold_score), abs(foothold_scores[1] - optimal_foothold_score)])


def score_new_move(holds, left, right, next_hold, next_hand, action_capabilities, verbose=VERBOSE) -> float:
    """Score a new move.

    This score is used as a cost in the generation process. A lower score is better and indicates a move that fits the action well.
    """
    # Check if action_capabilities has "weights" key
    if "weights" in action_capabilities:
        weights = action_capabilities["weights"]
    else:
        weights = {
            "power": 0.75,
            "finger_strength": 0.25,
            "footholds": 0.25,
        }
    # Costs range from 0 to 1, 1 indicates a bad fit, 0 indicates a good fit
    reach_cost = get_reach_cost(left, right, next_hold, next_hand, action_capabilities["reach"],
                                action_capabilities["power"],
                                action_capabilities["grade"])

    finger_cost = get_finger_cost(next_hold, action_capabilities["finger_strength"],
                                  action_capabilities["grade"])

    foothold_cost = get_footholds_cost(holds, left, right, next_hold, action_capabilities["core_strength"],
                                       action_capabilities["grade"], action_capabilities["power"])

    # Calculate the total cost
    cost = weights["power"] * reach_cost + weights["finger_strength"] * finger_cost + weights[
        "footholds"] * foothold_cost
    if reach_cost == 1.:
        return 1., reach_cost, finger_cost, foothold_cost
    # print(f"reach_cost: {reach_cost:.2f}, finger_cost: {finger_cost:.2f}, foothold_cost: {foothold_cost:.2f}, cost: {cost:.2f}")
    return cost, reach_cost, finger_cost, foothold_cost


def generate_route(action_capabilities, b=5, w=10, verbose=VERBOSE):
    """Generate a new route based on action capabilities."""
    # Create a sequence for each starting hold
    holds = get_all_holds()
    start_holds = get_start_holds(holds, action_capabilities)

    # Create a list of left and right start_holds as tuples, without duplicates
    start_holds = [(left_hold, right_hold) for left_hold in start_holds for right_hold in start_holds]
    start_hold_combinations = []
    for start_hold in start_holds:
        if start_hold not in start_hold_combinations:
            start_hold_combinations.append(start_hold)

    sequences = [
        Sequence([], holds, holds, start_holds[0], start_holds[1], score_new_move, action_capabilities) for
        start_holds in start_hold_combinations if
        get_coordinate_distance(start_holds[0], start_holds[1]) <= action_capabilities["reach"] * .5]

    complete = False
    while not complete:
        # Calculate the b best moves per sequence
        new_sequences = [new_sequence for sequence in sequences for new_sequence in sequence.get_b_best_sequences(b)]

        new_sequences.sort(key=lambda x: x.score)

        # Remove sequences that have the same holds
        no_duplicates_new_sequences = []
        no_duplicates_holds = []
        for new_sequence in new_sequences:
            if str(new_sequence.holds) not in no_duplicates_holds:
                no_duplicates_holds.append(str(new_sequence.holds))
                no_duplicates_new_sequences.append(new_sequence)

        # Check if the predicted grade matches the grade of the action capabilities
        # for sequence in no_duplicates_new_sequences:
        #     if sequence.complete and not sequence.predicted_grade:
        #         sequence.predict_grade()

        # Reduce the number of sequences
        sequences = no_duplicates_new_sequences[:w]

        # Check whether all sequences are already complete
        complete = all([sequence.complete for sequence in sequences])

    for n in range(1, 5):
        # Accept any route within a one-off grade, to minimize the time spent on grading generated routes.
        for seq_index, sequence in enumerate(sequences):
            if not sequence.predicted_grade:
                sequence.set_predicted_grade(predict_route_grade(sequence))
                print(f"Desired grade: {action_capabilities['font_grade']}, predicted grade: {sequence.predicted_grade}")
            if font_n_off(action_capabilities["font_grade"], sequence.predicted_grade, n):
                print(f"\nSuitable route found! Route {seq_index} is within {n} distance of desired grade.")
                print(f"Holds: {[coordinate_number_to_letter(hold) for hold in sequence.holds]}")
                print(f"Start holds: {[coordinate_number_to_letter(hold) for hold in sequence.start_holds]}")
                print(f"Action capabilities: {action_capabilities}")
                print(f"Goal: {action_capabilities['font_grade']}, predicted: {sequence.predicted_grade}\n")
                visualise_route(sequence.get_holds(), action_capabilities["font_grade"])
                return
    print("No sequence found :(")


def main():
    """Main function of the generation module."""
    all_action_capabilities = [
        # Power focus
        get_action_capabilities(10, 1.5, 1.1, 2, "6B+", {"power": 0.7, "finger_strength": 0.15, "footholds": 0.15}),
        get_action_capabilities(10, 1.9, 1.1, 2, "7A+", {"power": 0.7, "finger_strength": 0.15, "footholds": 0.15}),

        # Finger strength focus
        get_action_capabilities(10, 1.1, 1.5, 2, "6A+", {"power": 0.15, "finger_strength": 0.7, "footholds": 0.15}),
        get_action_capabilities(10, 1.1, 1.9, 2, "6C+", {"power": 0.15, "finger_strength": 0.7, "footholds": 0.15}),

        # Core focus
        get_action_capabilities(10, 1.1, 1.1, 5, "6B+", {"power": 0.15, "finger_strength": 0.15, "footholds": 0.7}),
        get_action_capabilities(10, 1.1, 1.1, 9, "6C+", {"power": 0.15, "finger_strength": 0.15, "footholds": 0.7}),
    ]
    for action_capabilities in all_action_capabilities:
        generate_route(action_capabilities)


if __name__ == "__main__":
    main()
