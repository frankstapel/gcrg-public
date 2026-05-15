from copy import deepcopy


class Sequence:
    """Sequence class for the beam search algorithm."""

    def __init__(self, holds, left_holds, right_holds, left_start, right_start, move_scorer, action_capabilities=None,
                 sequence=None, score=0., complete=False) -> None:
        """Initialise a sequence."""
        if sequence is None:
            sequence = []
        if not holds:
            holds = [left_start, right_start]
        self.holds = holds
        self.left_holds = left_holds
        self.right_holds = right_holds
        self.start_holds = [left_start, right_start]
        self.left = left_start
        self.right = right_start
        self.move_scorer = move_scorer
        self.action_capabilities = action_capabilities
        self.sequence = sequence
        self.score = score
        self.scores = []
        self.reach_costs = []
        self.finger_costs = []
        self.foothold_costs = []
        self.complete = complete
        self.predicted_grade = None

    def move(self, move, score) -> "Sequence":
        """Move to a new hold."""
        self.sequence.append(move)
        # Add the new hold to the list of holds if it is not already in the list
        if move[3] not in self.holds:
            self.holds.append(move[3])
        self.score += score[0]
        self.scores.append(score[0])
        if len(score) > 1:
            self.reach_costs.append(score[1])
            self.finger_costs.append(score[2])
            self.foothold_costs.append(score[3])
        if move[4] == "l":
            self.left = move[3]
            self.left_holds.remove(move[3])
        else:
            self.right = move[3]
            self.right_holds.remove(move[3])
        if move[3][1] == 17:
            self.complete = True
        return self

    def get_b_best_sequences(self, b) -> list["Sequence"]:
        """Get the b best scoring sequences out of all possible next moves."""
        if self.complete:
            return [self]
        # Create all moves
        moves = [[self.holds, self.left, self.right, left_hold, "l"] for left_hold in self.left_holds] + [
            [self.holds, self.left, self.right, right_hold, "r"] for right_hold in self.right_holds]

        # Score all moves
        if self.action_capabilities:
            scored_moves = [[move, self.move_scorer(*move, self.action_capabilities)] for move in moves]
        else:
            scored_moves = [[move, self.move_scorer(*move)] for move in moves]
        # Sort the moves by score
        scored_moves.sort(key=lambda x: x[1][0])
        scored_moves = scored_moves[:b]

        # Create new sequences with the scored moves
        return [deepcopy(self).move(*scored_move) for scored_move in scored_moves]

    def get_holds(self) -> list:
        """Get the holds from a sequence."""
        return self.sequence[0][1], self.sequence[0][2], *[move[3] for move in self.sequence]

    def set_predicted_grade(self, grade) -> str:
        """Predict the grade of a sequence."""
        # self.predicted_grade = predict_route_grade(self.sequence)
        self.predicted_grade = grade
        return self.predicted_grade
