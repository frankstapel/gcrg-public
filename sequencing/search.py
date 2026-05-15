from sequencing.sequence import Sequence
from sequencing.move_scoring import score_move


def beam_search(holds, route_index, b=3, w=5):
    """ Search for the best sequence on the given holds using Beam Search.

    :param holds: Holds used to determine the sequence
    :param route_index: Index of route for which search is being applied
    :param b: branching factor
    :param w: beam width
    :return: Best sequence
    """
    print(f"Beam searching for route {route_index}")

    # Create a sequence for each starting hold
    start_holds = [hold for hold in holds if hold[1] <= 5]
    sequences = [Sequence(holds, holds, holds, start_holds[left], start_holds[right], score_move) for left in
                 range(len(start_holds)) for right in range(len(start_holds))]

    complete = False
    while not complete:
        # Calculate the b best moves per sequence
        new_sequences = [new_sequence for sequence in sequences for new_sequence in sequence.get_b_best_sequences(b)]

        # Reduce the number of sequences
        new_sequences.sort(key=lambda x: x.score)
        sequences = new_sequences[:w]

        # Check whether all sequences are already complete
        complete = all([sequence.complete for sequence in sequences])

    return [sequences[0].sequence, sequences[0].score]
    # Return a sequence with a list of moves that can be used in classification


def main():
    holds = [[0, 3], [1, 3], [2, 6], [3, 8], [5, 11], [3, 14], [5, 17]]
    print(beam_search(holds, 0, 3, 5))


if __name__ == "__main__":
    main()
