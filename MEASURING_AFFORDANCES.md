# Measuring Affordances for gcrg-public

This document describes how to measure the climbing affordances used by the route generator:
- `reach`
- `finger_strength`
- `power`
- `core_strength`
- `grade`

It is based on the questionnaire design used in the user studies.

## 1. Required setup

- Use a MoonBoard with the 2017 hold setup if available.
- Warm up thoroughly before testing.
- Perform each strength test for a maximum of three attempts.
- Stop if any exercise feels unsafe or uncomfortable.

## 2. Body measurements

Measure the following values before strength testing:

- `height` in centimeters
- `arm span` in centimeters
- `weight` in kilograms

Suggested method:
- Lie flat on the ground with one side touching a wall.
- Push an object away from the wall with the other hand.
- Measure the distance between the wall and the object.
- A climbing shoe, brush, or chalk bag is a suitable object for this measurement.

## 3. Reach

The `reach` affordance is a board-based reach value measured in holds.

- Use your normal MoonBoard reach without tape.
- It represents how far you can comfortably reach between holds.
- In the route generator, `reach` is used directly to determine whether a move distance is within your physical reach.

## 4. Finger strength

Measure `finger_strength` using a maximum hang on a 20mm edge.

- Perform a 7-second hang on a 20mm edge.
- Record the maximum weight you can hold, including your bodyweight.
- The repository represents this affordance as a body weight ratio, so a stronger hang yields a higher value.

## 5. Power

Measure `power` with a weighted pull-up test.

- Perform a one-repetition maximum pull-up.
- Include your bodyweight in the total weight.
- Record the maximum successful weight.
- This value is converted to a relative scale for the route generator.

## 6. Core strength

Measure `core_strength` using an isometric core hold score.

Evaluate the highest scoring exercise you can perform from the following table:

- None: 0
- L-sit (bend knees) 10 sec: 1
- L-sit (bend knees) 20 sec: 2
- L-sit (bend knees) 30 sec: 3
- L-sit 10 sec: 4
- L-sit 15 sec: 5
- L-sit 20 sec: 6
- Front lever 5 sec: 7
- Front lever 10 sec: 8
- Front lever 20 sec: 9
- Front lever 30 sec: 10

The repository converts `core_strength` into a normalized score by dividing the selected value by 10.

## 7. Grade

Collect self-reported grade information as part of the climber profile:

- Maximum MoonBoard grade.
- Preferred boulder style.
- Estimated grade for test routes.

The route generator uses a normalized grade value to match target difficulty.

## 8. Route testing notes

When validating generated routes:

- Try each route within up to three attempts.
- Record whether the route was completed.
- If possible, write down the hold sequence and hand order used.
- Compare your perceived route grade, flow, and quality with the generated route.
