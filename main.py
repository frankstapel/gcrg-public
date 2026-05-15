from classification import hold_scores
from sequencing import move_scoring
from sequencing import route_sequencer


def main():
    # 1. Calculate hold scores from input routes (hold_scores.py)
    hold_scores.main()

    # 2. Train move difficulty model (move_scoring.py)
    move_scoring.main()

    # 3. Generate optimal sequences for each route (route_sequencer.py)
    route_sequencer.main(False)


if __name__ == "__main__":
    main()
