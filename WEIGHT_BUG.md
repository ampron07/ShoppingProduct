# Slider weight regression

The user reported selecting price weight 0.65 but seeing scores and explanations
for 0.50/0.50. Source inspection showed no hardcoded scoring weight: the same
slider variable was passed to ranking and displayed in explanations.

The original slider was inside a Streamlit form without an explicit state key.
A new AppTest regression first submitted at 0.50, then updated the slider to
0.65 with a separate rerun, then submitted Search. Before the fix, a spy around
the real ranking function observed price_weight=0.50 rather than 0.65:
`1 failed, 6 passed` for the interface tests. This reproduced a state-loss path
across separate reruns; it does not establish the exact browser event sequence
in the user's session.

The correction moves the slider outside the batched form with an explicit
`price_weight` key so slider reruns persist the selected value before Search.
Rating weight is derived once as `1 - price_weight` and reused for scoring and
explanations. A selected-weight caption makes the pending choice visible.
Changing the slider clears submitted results until Search is clicked again.

`test_resubmit_065_updates_ranking_and_every_explanation` checks actual ranking
arguments, the 65%/35% results caption, every component explanation, and exact
displayed scores for a controlled two-product fixture: 0.7900 and 0.3500. It
then changes to 0.20/0.80 and verifies updated scores 0.8000 and 0.5200, guarding
against values sticking across subsequent searches.

After correction: `python -m pytest tests -q` reported
`91 passed, 9 subtests passed in 3.69s`. Stage 1 and filtering tests also passed.
These are automated mocked-data results; browser confirmation by the student
is still pending. No claim is made about reproducing the user's exact live
scores without their dataset and conditions.
