# Grade Combiners: Horizontal and Vertical

This document explains how route-grade prediction combines move-level probability outputs from ordinal decision models. It covers the mathematics, the implementation strategy, and the reasons why the two combiner designs are useful.

## 1. Single-move grading

Each move in a route is represented by a probability vector from ordinal models:

- Let `m` index a move.
- Let `i` index adjacent ordinal grade decision models.
- Let `p_{m,i}` be the probability output of model `i` for move `m`.

The trained move model produces a probability for each grade boundary, so the vector length is `len(USED_GRADES) - 1`.

### Grade prediction for one move

The move grade is predicted from the ordinal model output by looking for the strongest boundary signal.

- Each probability `p_{m,i}` is the model's output for one grade boundary on move `m`.
- Compare adjacent boundary probabilities to find the biggest jump:

  `Δ_{m,i} = | p_{m,i+1} - p_{m,i} |`

- The predicted grade index is the boundary with the largest jump:

  `g_m = argmax_i Δ_{m,i}`

- Convert `g_m` back to a grade label using the repository's grade conversion functions.

### Why the largest jump?

The ordinal model is not directly predicting a grade label. It produces a set of boundary probabilities, and the largest adjacent jump shows where the model's opinion changes most sharply.

- If two adjacent probabilities are similar, the model is uncertain between those boundaries.
- If one adjacent pair has a much larger gap, that boundary is where the model is most confident the move crosses a difficulty threshold.
- Choosing the largest jump is like finding the clearest breakpoint in the sequence of boundary probabilities.

This is easier to understand with an example:

- Suppose a move has probabilities [0.1, 0.2, 0.8, 0.9].
- The biggest jump is between 0.2 and 0.8.
- That means the model is most confident that the move's true grade sits at the boundary after the second probability.

So the rule chooses the grade boundary with the strongest signal instead of averaging weak signals across all boundaries.

## 2. Horizontal combiner

The horizontal combiner works in two stages:

1. Predict a grade for each move independently using the single-move rule.
2. Average those move grades to produce the route grade.

### Implementation details

Given a route with moves `M`:

- For each move `m ∈ M`, compute `g_m = font_to_index(grader(p_m))`.
- Sort the move grade indices in descending order (hardest first).
- Optionally select only the top `N` hardest moves, or skip the top `k` hardest moves.
- Compute the route grade index as:

  `G_route = round( mean( g_m for selected moves ) )`

- Convert `G_route` back to a route grade label.

### In code

The horizontal combiner is implemented in `classification/route_scores.py` as `combine_moves_horizontal`.

### Why this is good

- It preserves the per-move difficulty signal.
- It makes the route grade sensitive to the distribution of move difficulties across the entire route.
- Averaging reduces the effect of noisy single-move predictions.
- Using only the top N hardest moves focuses the route grade on the crux of the route.

## 3. Vertical combiner

The vertical combiner aggregates probabilities before predicting a route grade.

### Implementation details

Given a route with moves `M`:

- Compute the average probability for each decision model across all selected moves:

  `p_i = (1 / |M|) * sum( p_{m,i} for m in M )`

- Compute adjacent differences on the averaged probabilities:

  `Δ_i = | p_{i+1} - p_i |`

- Choose the grade boundary index with the largest averaged jump:

  `G_route = argmax_i Δ_i`

- Convert the resulting index back to a grade label.

### In code

The vertical combiner is implemented in `classification/route_scores.py` as `combine_moves_vertical`.

### Why this is good

- It pools evidence across the whole route before making a grade decision.
- It is more robust when individual move predictions are noisy.
- It captures a global route difficulty signal instead of treating moves independently.
- It can reduce the influence of outlier move predictions by smoothing probabilities.

## 4. Top-N and skip-hardest variants

Both combiners support two variants:

- `top N` only: use only the `N` hardest moves in the combination.
- `skip_top k`: remove the `k` hardest moves before combining.

These variations help adapt the route grade prediction to different assumptions:

- Using the top N moves emphasizes the route's hardest section.
- Skipping the hardest move can reduce the effect of an outlier or an unusually difficult crux move.

The implementation in `classification/route_scores.py` uses `take_top` to apply these filters uniformly to both horizontal and vertical combinations.

## 5. Model selection with grid search

The code performs a grid search over:

- combiner type: `horizontal` or `vertical`
- top selection: values `1..5` and `-1` for all moves
- skip selection: values `0..4`

The grid search is executed in `predict_route_grades()` and evaluates each combination against the ground-truth route grades.

## 6. Summary

- Horizontal combiner: move-level grades first, then average.
- Vertical combiner: average model probabilities first, then predict route grade.
- The key mathematical idea is the same in both cases: choose the grade boundary with the largest adjacent probability gap.
- The difference is whether the route grade is built from individual move grades or from pooled model evidence.
- Both methods are useful because they trade off local move detail against route-level stability.
