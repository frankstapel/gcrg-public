# Scores and Costs in gcrg-public

This document explains the scores and costs calculated by the repository, why they exist, and how they work.

## 1. Overview

The repository computes several different values:

- `grade` and normalized grade values for route difficulty
- `hold_score` for each hold on the board
- move-level scores for distance, finger difficulty, footholds, and flow
- route-generation costs for reach, finger strength, and core/foothold fit

### Scores vs costs

- A **score** is a descriptive measure of difficulty or quality. Examples include `hold_score` and move-level scores such as `score_distance`.
- A **cost** is a penalty value used for optimization. In this repository, costs are minimized by the route generator.
- In practice, many move-level scoring functions return lower-is-better values, so they behave like penalties even when they are named `score_*`.

A key design principle is that low cost means a better fit for the climber, while high cost means a poorer fit or an invalid move.

The overall goal is to turn climbing route data and user capabilities into numerical values that can be compared consistently and used to generate suitable routes.

## 2. Route and Hold Scores

### Grade conversion and normalization

Routes are labeled with Font grades such as `6A+`, `7B`, `7C+`, etc. The code converts these grades into:

- `ordinal_grade` – an ordinal encoding of the Font grade
- `IRCRA_grade` – converted International Climbing and Rock Climbing Association grade
- `normalized_IRCRA_grade` – scaled to the range [0, 1]
- `font_index` – numeric index for the Font grade
- `normalized_grade` – scaled Font index in [0, 1]

Normalizing grades makes them comparable and makes it easier to compute averages and distances.

### Hold scores (`classification/hold_scores.py`)

A hold score is derived from the routes that use that hold:

- Each route is converted to a normalized grade
- Each hold is assigned the average normalized grade of routes that include it
- The hold score is then scaled to `[0, 1]` across all holds

The result is:

- `number_of_routes` – how many routes used that hold
- `grade_avg` – average normalized route grade for that hold
- `grade_std` – standard deviation of route grade for that hold
- `hold_score` – normalized difficulty score for that hold

Why it matters: the system assumes a hold is harder when it appears more often in harder routes, and easier when it appears more often in easier routes.

## 3. Move-Level Scores

These scores are used when evaluating or training move models. In this repository, many move-level scoring functions return lower-is-better values, so they behave like penalties even though they are named as scores.

### Distance score (`score_distance`)

This score measures how far the next hold is relative to the current hand positions.

- The move center is the midpoint between the two current hands
- `distance` is the distance from that center to the next hold
- A normal distribution is used to define an ideal distance
- The score is computed as:

```python
1 - norm.pdf(distance, ideal, sigma) / norm.pdf(ideal, ideal, sigma)
```

This means:

- `0.0` is best (distance equals the ideal)
- values near the ideal distance are low
- larger deviations are penalized smoothly
- if the move is unreachable or downward, the score is forced toward `1.0`

### Finger score (`score_fingers`)

This combines hold difficulty scores for the current left hand, current right hand, and next hold:

```python
np.mean([left_score, right_score, next_score])
```

It captures the idea that a move is easier when the involved holds are easier.

### Foothold availability score (`score_foothold` and `score_footholds`)

The foothold scoring evaluates whether there are good feet positions available for the next move.

#### Single foothold score

- An optimal foothold distance is assumed to be around `2/3` of the climber's reach.
- The code computes the foothold distance from the center of the hands.
- A normal-distribution penalty is used again:

```python
distance_score = 1 - norm.pdf(distance, optimal_reach, sigma)
```

- That distance score is multiplied by the foothold's hold difficulty
- This means good footholds are those that are both reachable and reasonably easy

#### Footholds availability score

- The code gathers visible footholds and kickboard footholds
- It filters out holds already used by the hands and holds that are too high
- It keeps footholds within reach
- It computes scores for all candidate footholds
- It then averages the two best foothold scores

This gives a measure of how well-supported a move is by possible foot positions.

## 4. Move Generation Costs

The generation module converts user abilities into action capabilities, then uses those to score candidate moves.

In this section, the values are explicitly called costs because they are penalties for route generation. Cost values are normalized to lie between `0` and `1` wherever possible, with `0` meaning a perfect fit and `1` meaning a poor or invalid move.

The move-scoring functions in the previous section produce low-is-better values, and the generation module combines them as formal costs.

### User affordances to action capabilities

The user-provided inputs are:

- `grade` – self-indicated difficulty based on the climber's own board route history
- `reach` – board-based reach measured in holds
- `finger_strength` – MBW% one-rep hang for 7 seconds on 20mm edge
- `power` – MBW% for one pull-up
- `core_strength` – static hold time translated into a score from 0 to 10

These are converted to normalized values:

- reach stays in hold units
- power becomes `(power - 1) / 1.2`
- finger strength becomes `(finger_strength - 1) / 1.2`
- core strength becomes `core_strength / 10`
- grade becomes a normalized generation grade via a mapped IRCRA scale

That means the code treats each capability as a value roughly between 0 and 1.

### Reach cost (`get_reach_cost`)

This cost compares the move distance to an `optimal_reach` that depends on the climber's:

- reported `reach`
- `power`
- desired `grade`

The formula is:

```python
optimal_reach = 1 + reach * 0.3 + grade * 2 + power * 4
```

Then it uses a normalized normal PDF centered on `optimal_reach`:

```python
reach_cost = 1 - norm.pdf(moving_distance, optimal_reach, 2) / norm.pdf(optimal_reach, optimal_reach, 2)
```

Additional hard constraints return a cost of `1.0` (bad) if:

- the move is outside the climber's reach
- the move is too small or too low
- the move goes downward instead of upward

### Finger cost (`get_finger_cost`)

This cost compares the next hold's difficulty to the climber's effective finger capacity.

- `next_score` is the hold score of the next hold
- `finger_strength` is blended with the desired grade to represent both the climber's action capability and the intended difficulty:

```python
finger_strength = finger_strength * 0.5 + grade * 0.5
```

- The cost uses a normalized normal PDF around that value:

```python
1 - norm.pdf(next_score, finger_strength, 0.3) / norm.pdf(finger_strength, finger_strength, 0.3)
```

This means holds near the climber's combined capacity-and-target-difficulty estimate are best, with larger deviations penalized.

### Foothold cost (`get_footholds_cost`)

This cost evaluates how well the move is supported by footholds.

- It finds available footholds near the current hand center
- It computes a foothold score for each candidate
- It keeps the two best footholds
- It calculates an optimal foothold score from:

```python
optimal_foothold_score = core_strength * 0.75 + grade * 0.25
```

- The cost is the average absolute difference between the two best footholds and the optimal foothold score

This means moves are penalized when foot support is worse than expected for the climber's core strength and target grade.

### Total move cost (`score_new_move`)

The generation module combines the three costs into a single move cost:

```python
cost = power_weight * reach_cost + finger_weight * finger_cost + footholds_weight * foothold_cost
```

Weights are chosen from action capability preferences, so the route generator can prioritise:

- reach/power
- finger strength
- foothold/core support

A cost of `0` means a very good fit for the climber, while `1` means a poor or invalid move.

## 5. Why this works

### Smooth penalties with `norm.pdf`

The repository uses normal probability density functions to create smooth, continuous penalties rather than binary pass/fail decisions. The normal PDF is:

```math
\text{norm.pdf}(x, \mu, \sigma) = \frac{1}{\sigma \sqrt{2\pi}} \, e^{-\frac{(x-\mu)^2}{2\sigma^2}}
```

Where:

- `x` is the observed value (for example, actual move distance or hold difficulty)
- `\mu` is the ideal value (the target distance or expected strength)
- `\sigma` controls how quickly the penalty grows away from `\mu`

In the code, the cost is usually computed by normalizing the PDF at `x` by the PDF at `\mu` and subtracting from 1:

```python
cost = 1 - norm.pdf(x, mu, sigma) / norm.pdf(mu, mu, sigma)
```

This has the following mathematical meaning:

- `norm.pdf(mu, mu, sigma)` is the maximum PDF value, so the division produces a value in `(0, 1]`
- when `x = mu`, the cost becomes `0`
- as `x` moves away from `mu`, the PDF gets smaller and the cost grows toward `1`
- `sigma` determines the width of the acceptable range around `mu`
- because the exponent uses `(x - mu)^2`, deviations are penalized by the square of the distance, so large mismatches grow much faster than small ones

In plain terms:

- the formula defines an “ideal” value `mu`
- values close to that ideal are almost free
- moderate deviations are penalized gently
- large deviations are penalized strongly
- the cost always stays between `0` and `1`, making it easy to compare different types of move penalties

That means:

- moves close to the ideal are scored gently
- moves far from the ideal are penalized more strongly
- the result is easy to compare across different move types

### Hold score as a proxy for difficulty

Hold scores are derived from route grades. This makes sense because:

- harder routes tend to use harder holds
- easier routes tend to use easier holds
- a hold's difficulty is therefore learned from the data instead of being hand-labeled

### Combining body capabilities and route difficulty

The generation model does not use raw physical measurements directly. Instead, it maps them into relative action capabilities and then compares each candidate move with those capabilities. This is a heuristic penalty model based on the author's experienced judgement: it combines the climber's action capability with the intended route difficulty to estimate how suitable a move is.

That means the generator can answer questions like:

- “Is this distance reasonable for this climber?”
- “Is this hold difficulty appropriate given their finger strength and target route grade?”
- “Does this move have enough foothold support for the climber's core?”

## 6. How the system fits your affordances

Your affordances are directly represented in the generation module:

- `reach` → physical hold-to-hold reach without tape
- `finger_strength` → MBW% hang strength on 20mm
- `power` → MBW% pull-up strength
- `core_strength` → static hold capability converted to a 0–10 scale
- `grade` → self-reported climbing difficulty

The system uses those values to compute:

- reachability cost: whether the reach is appropriate
- finger cost: whether the next hold difficulty matches strength
- foothold cost: whether the move has adequate foot support

## 7. Practical interpretation

- Lower cost is better. A move that matches the climber is close to `0`.
- Higher cost is worse. A cost of `1` usually means the move is invalid or too hard.
- These scores are combined so the generator can choose moves that fit the climber and the target grade.

## 8. Modules and where each score appears

- `classification/hold_scores.py`
  - `hold_score`
  - route-grade normalization

- `sequencing/move_scoring.py`
  - `score_distance`
  - `score_fingers`
  - `score_foothold`
  - `score_footholds`
  - move-level scoring used for sequenced routes

- `generation/generation.py`
  - `get_action_capabilities`
  - `get_reach_cost`
  - `get_finger_cost`
  - `get_footholds_cost`
  - `score_new_move`

- `classification/route_scores.py`
  - route grade prediction using move score features

## 9. Summary

This code turns route grades and physical capabilities into a set of comparable numerical costs. Those costs are used to:

- classify holds
- score individual moves
- generate routes that better fit a climber's measured abilities

The main design principle is to use smooth, normalized scoring functions so the system can evaluate many candidate moves and choose the best fit for a climber’s profile.
